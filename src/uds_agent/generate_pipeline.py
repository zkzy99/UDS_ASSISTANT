"""测试用例生成管道。Excel → 文本 → LLM 直接生成用例 → 解析输出。"""

from __future__ import annotations

import hashlib
import logging
import re
import time
from datetime import datetime
from pathlib import Path

import yaml

from .llm_client import LLMClient, LLMResponse
from .pipeline import ExtractionOutput, UDSExtractionPipeline
from .prompt_loader import (
    SERVICE_NAMES,
    build_generation_user_message,
    build_sheet_name,
    load_generation_config,
    load_service_prompt,
)
from .test_parser import parse_summary, parse_test_cases
from .test_schemas import ServiceTestResult

logger = logging.getLogger("generate_pipeline")

_LOG_DIR = Path(__file__).parent.parent.parent / "logs"/ "llm_raw"


def _build_diagnostics(
    extraction: ExtractionOutput,
    llm_response: LLMResponse | None,
    total_elapsed: float,
) -> dict:
    return {
        "timing": {
            "extraction_seconds": round(extraction.elapsed_seconds, 2),
            "generation_seconds": round(llm_response.elapsed_seconds, 2) if llm_response else 0,
            "total_seconds": round(total_elapsed, 2),
        },
        "excel_input": {
            "text_length": extraction.excel_text_length,
            "sheets_filtered": extraction.sheets_filtered,
        },
        "errors": extraction.errors,
    }


class UDSGeneratePipeline:
    """生成管道：读取 Excel 文本 → 加载提示词 → LLM 生成 → 解析输出。"""

    def __init__(self, config_path: str = "config.yaml"):
        self._extract_pipeline = UDSExtractionPipeline(config_path=config_path)
        self._generate_client = LLMClient.from_config(
            config_path=config_path, task="generate"
        )
        self._config_path = config_path
        self._gen_config = load_generation_config(config_path)
        self._cache_cfg = self._load_cache_config()

    def _load_cache_config(self) -> dict:
        cfg_path = Path(self._config_path)
        if cfg_path.exists():
            cfg = yaml.safe_load(cfg_path.read_text(encoding="utf-8")) or {}
        else:
            cfg = {}
        cache = cfg.get("cache", {})
        return {
            "enabled": cache.get("enabled", False),
            "dir": cache.get("dir", "cache"),
        }

    @staticmethod
    def _cache_key(excel_path: str, service_id: str, domain: str, cache_dir: str) -> Path:
        md5 = hashlib.md5(Path(excel_path).read_bytes()).hexdigest()
        return Path(cache_dir) / f"{md5}_{service_id}_{domain}.json"

    @staticmethod
    def _replace_p2_placeholder(content: str, params: dict | None, service_id: str) -> str:
        """将 LLM 输出中的 XX XX XX XX 替换为 P2/P2* 对应的 hex 值。

        替换规则（仅当 P2 和 P2* 都合法时才替换）：
          P2   → 2字节 hex（大端）
          P2*  → (P2*/10) → 2字节 hex（大端）
          示例：P2=50, P2*=1000 → "00 32 00 64"
        """
        if not params:
            return content

        p2_raw = params.get("P2")
        p2s_raw = params.get("P2*")
        if p2_raw is None or p2s_raw is None:
            return content

        try:
            p2 = int(p2_raw)
            p2s = int(p2s_raw)
        except (ValueError, TypeError):
            logger.warning(f"[{service_id}] P2/P2* 参数不是合法整数: P2={p2_raw}, P2*={p2s_raw}")
            return content

        if not (0 <= p2 <= 65535 and 0 <= p2s <= 65535):
            logger.warning(f"[{service_id}] P2/P2* 超出范围(0-65535): P2={p2}, P2*={p2s}")
            return content

        p2_hex = f"{p2:04X}"
        p2s_hex = f"{p2s // 10:04X}"
        replacement = f"{p2_hex[:2]} {p2_hex[2:]} {p2s_hex[:2]} {p2s_hex[2:]}"

        result = re.sub(r'\bXX\s+XX\s+XX\s+XX\b', replacement, content)
        if result != content:
            logger.info(f"[{service_id}] P2 占位符已替换: {replacement} (P2={p2}, P2*={p2s})")
        return result

    @staticmethod
    def _renumber_case_ids(content: str, service_id: str) -> str:
        """将 LLM 输出中的 Case ID 按出现顺序重新编号。

        格式：Diag_{service_id}_{Fun|Phy}_{NNN}
        Fun 和 Phy 分别独立编号，从 001 开始。
        """
        pattern = re.compile(rf'Diag_{re.escape(service_id)}_(Fun|Phy)_(\d{{3}})')
        counters = {"Fun": 0, "Phy": 0}

        def _replace(match: re.Match) -> str:
            addr_type = match.group(1)
            counters[addr_type] += 1
            new_seq = f"{counters[addr_type]:03d}"
            return f"Diag_{service_id}_{addr_type}_{new_seq}"

        result, count = pattern.subn(_replace, content)
        if count > 0:
            logger.info(
                f"[{service_id}] Case ID 重编号完成: "
                f"Fun={counters['Fun']}条, Phy={counters['Phy']}条, 共替换{count}处"
            )
        return result

    def generate(
        self,
        excel_path: str,
        service_id: str,
        domain: str = "App",
        original_filename: str = "",
        author: str = "",
        params: dict | None = None,
    ) -> ServiceTestResult:
        """执行完整的生成管道。"""
        start = time.time()

        # 缓存检查
        cache_path = None
        if self._cache_cfg["enabled"]:
            cache_path = self._cache_key(excel_path, service_id, domain, self._cache_cfg["dir"])
            if cache_path.exists():
                logger.info(f"[{service_id}] cache hit: {cache_path.name}")
                return ServiceTestResult.model_validate_json(cache_path.read_text(encoding="utf-8"))
            if cache_path.exists():
                logger.info(f"[{service_id}] cache hit: {cache_path.name}")
                return ServiceTestResult.model_validate_json(cache_path.read_text(encoding="utf-8"))

        # 1. 读取 Excel 文本
        logger.info(f"[{service_id}] 读取 Excel 文本...")
        extraction = self._extract_pipeline.extract(
            excel_path=excel_path,
            service_id=service_id,
            software_domain=domain,
            original_filename=original_filename,
        )

        if extraction.errors:
            logger.warning(f"[{service_id}] Excel 读取有错误: {extraction.errors}")

        logger.info(
            f"[{service_id}] Excel读取完成 文本长度: {extraction.excel_text_length} 字符"
        )

        # 2. 加载服务提示词
        try:
            service_prompt = load_service_prompt(service_id, self._config_path)
        except FileNotFoundError as e:
            elapsed_err = time.time() - start
            return ServiceTestResult(
                service_id=service_id,
                service_name=SERVICE_NAMES.get(service_id.lower(), ""),
                sheet_name=build_sheet_name(service_id),
                meta={
                    "error": str(e),
                    "elapsed_seconds": elapsed_err,
                    "extraction_diagnostics": _build_diagnostics(extraction, None, elapsed_err),
                },
            )

        # 3. 构建 user message（直接使用 Excel 原始文本）
        user_message = build_generation_user_message(
            excel_text=extraction.excel_text,
            service_id=service_id,
        )

        logger.info(
            f"[{service_id}] 提示词加载完成，user message 长度: {len(user_message)}"
        )

        # 4. 调用 LLM 生成用例
        llm_response: LLMResponse | None = None
        max_tokens = self._gen_config.get("max_tokens", 32000)

        try:
            llm_response = self._generate_client.chat(
                system_prompt=service_prompt,
                user_message=user_message,
                temperature=0.05,
                max_tokens=max_tokens,
            )
            logger.info(
                f"[{service_id}] LLM 生成完成 ({llm_response.elapsed_seconds:.1f}s, "
                f"{llm_response.usage.get('total_tokens', 0)} tokens)"
            )
        except RuntimeError as e:
            logger.error(f"[{service_id}] LLM 不可用: {e}")
            elapsed_err = time.time() - start
            return ServiceTestResult(
                service_id=service_id,
                service_name=SERVICE_NAMES.get(service_id.lower(), ""),
                sheet_name=build_sheet_name(service_id),
                meta={
                    "error": str(e),
                    "elapsed_seconds": elapsed_err,
                    "extraction_diagnostics": _build_diagnostics(extraction, None, elapsed_err),
                },
            )

        # 5. 保存 LLM 原始输出（调试用）
        _LOG_DIR.mkdir(exist_ok=True)
        _ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        _safe_name = original_filename.replace(" ", "_") if original_filename else "unknown"
        _raw_log = _LOG_DIR / f"{_ts}_{service_id}_{_safe_name}_llm_raw.md"
        _raw_log.write_text(llm_response.content, encoding="utf-8")
        logger.info(f"[{service_id}] LLM 原始输出已保存: {_raw_log}")

        # 6. 替换 XX XX XX XX 占位符（基于 P2/P2* 参数）
        content = self._replace_p2_placeholder(llm_response.content, params, service_id)

        # 7. 重编号 Case ID
        content = self._renumber_case_ids(content, service_id)

        # 8. 解析输出
        test_cases = parse_test_cases(content, service_id)
        summary = parse_summary(content)

        # 7. 填充配置字段
        author = author or self._gen_config.get("author", "")
        design_method = self._gen_config.get("design_method", "")
        precondition = self._gen_config.get("precondition", "")
        sys_req_id = self._gen_config.get("system_requirement_id", "")

        for tc in test_cases:
            tc.author = author
            tc.design_method = design_method
            tc.precondition = precondition
            tc.system_requirement_id = sys_req_id

        elapsed = time.time() - start
        logger.info(
            f"[{service_id}] 生成完成: {len(test_cases)} 条用例, {elapsed:.1f}s"
        )

        sid_key = service_id.lower()
        service_name = SERVICE_NAMES.get(sid_key, "")

        result = ServiceTestResult(
            service_id=service_id,
            service_name=service_name,
            sheet_name=build_sheet_name(service_id),
            total_count=len(test_cases),
            test_cases=test_cases,
            sections_summary=summary,
            meta={
                "provider": llm_response.provider if llm_response else "unknown",
                "model": llm_response.model if llm_response else "unknown",
                "elapsed_seconds": round(elapsed, 2),
                "llm_tokens": llm_response.usage.get("total_tokens", 0) if llm_response else 0,
                "extraction_diagnostics": _build_diagnostics(extraction, llm_response, elapsed),
            },
        )

        # 8. 写入缓存
        if cache_path is not None:
            cache_path.parent.mkdir(parents=True, exist_ok=True)
            cache_path.write_text(result.model_dump_json(), encoding="utf-8")
            logger.info(f"[{service_id}] 缓存已写入: {cache_path.name}")

        return result
