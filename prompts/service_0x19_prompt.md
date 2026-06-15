# Service 0x19 ReadDTCInformation — 用例生成规则

## 服务概述

- **Service ID**: 0x19
- **Service Name**: ReadDTCInformation
- **正响应 SID**: 0x59
- **负响应格式**: `7F 19 <NRC>`
- **无 Subfunction 概念但有子功能编号**（0x01/0x02/0x04/0x06/0x0A 等），SPRMIB 不适用
- **关键特性**: 各子功能有不同的请求/响应格式；需要 DTC 表数据支撑；需按逐 DTC 生成故障注入用例
- **NRC 优先级链**：共享 Figure 6，追加 0x31（DTC 编号或 Record Number 越界）
- **完整链**: 0x13 > 0x12 > 0x31

### 各子功能正响应格式

| 子功能 | 名称 | 请求格式 | 正响应格式 |
|--------|------|---------|-----------|
| 0x01 | ReportNumberOfDTCByStatusMask | `19 01 <DTCStatusMask>` | `59 01 <AvailabilityMask> <NumberOfDTC_H> <NumberOfDTC_L>` |
| 0x02 | ReportDTCByStatusMask | `19 02 <DTCStatusMask>` | `59 02 <AvailabilityMask> <DTC_3bytes> <Status_1byte> [...]` |
| 0x04 | ReportDTCSnapshotRecordByDTCNumber | `19 04 <DTC_3bytes> <SnapshotRecordNumber>` | `59 04 <DTC_3bytes> <Status> <SnapshotRecordNumber> <data>` |
| 0x06 | ReportDTCExtendedDataRecordsByDTCNumber | `19 06 <DTC_3bytes> <ExtendedDataRecordNumber>` | `59 06 <DTC_3bytes> <Status> <RecordNumber> <data>` |
| 0x0A | ReportSupportedDTCs | `19 0A FF` | `59 0A <DTCStatusAvailabilityMask> <DTC_3bytes> <Status> [...]` |

### 典型 NRC

均在共享 NRC 编码速查表中，无 0x19 专有补充。

---

## 生成分类（共 7 类）

按以下固定顺序逐类生成，每个分类使用 `## N.N` 作为标题（如 `## 1.1 Session Layer Test`）。

### 软件域规则

见共享文件。若 Boot 域存在 0x19 数据，则为 Boot 域单独生成 Physical + Functional（如支持）的完整用例。

### 寻址方式规则

**即使参数表 `Functional Request = N`，仍需生成完整的 Functional 寻址用例集。** 此时所有 Functional 用例的预期输出统一为 `Check No_Response Within[1000]ms;`。

---

### 分类 1: Session Layer Test
#### 用例数量规则

- `Nmask` = 需测试的 DTCStatusMask 值数量（通常为 3：FF / 0x08 / 0x09）
- `Npos` = 支持的子功能（0x01/0x02） × 支持的会话数 × Nmask
- `Npos_0A` = 0x0A 子功能 × 支持的会话数（0x0A 不区分 Mask）
- `Nneg_sf` = 不支持的子功能 case 数
- `Nneg_sess` = 不支持的会话 case 数
- **总数 = Npos + Npos_0A + Nneg_sf + Nneg_sess**

> **关键规则**：对于 0x01 和 0x02 子功能，**必须测试多个 DTCStatusMask 值**：
> - `FF`（查询所有状态位）
> - `0x08`（仅查询 confirmedDTC，bit3=1）
> - `0x09`（查询 testFailed 或 confirmedDTC，bit0+bit3）
>
> 这些 Mask 值来自输入表 `GroupOfDTC` 中被标记为 `Support=Y` 的状态位组合。

#### 用例命名规则

- 正向：`<CurrentSessionName> Session support the 0x19 service 0x<Sub> subfunction`
  - 示例：`Extended Session support the 0x19 service 0x02 subfunction`
- 负向（会话不支持）：`<CurrentSessionName> Session nonsupport 0x19 services`
  - 示例：`Default Session nonsupport 0x19 services`
- 负向（子功能不支持）：`0x19 service nonsupport 0x<Sub> subfunction`
  - 示例：`0x19 service nonsupport 0x03 subfunction`

#### 测试步骤模板

**⚠️ test_procedure 中只写 Send/Delay/Stop/Resume 操作，绝对不要写 Check 语句！步骤编号严格使用 `N. ` 格式，禁止使用 `StepN:` 格式。**

**A. 当前会话不支持 0x19 服务 — Default 会话（负向）**
```
1. Send DiagBy[Physical]Data[10 01];
2. Send DiagBy[Physical]Data[19 <RepSub> <DTCStatusMask>];
```

**B. 支持子功能正向（需 DTC 数据）— Extended 会话**
```
1. Send DiagBy[Physical]Data[10 01];
2. Send DiagBy[Physical]Data[10 03];
3. Stop MsgCycle[<FaultMsgId>];
4. Delay[3000]ms;
5. Send DiagBy[Physical]Data[19 <Sub> <DTCStatusMask>];
6. Send MsgCycle[<FaultMsgId>];
```

**C. 支持子功能正向（不需 DTC 数据如 0x01/0x0A）— Extended 会话**
```
1. Send DiagBy[Physical]Data[10 01];
2. Send DiagBy[Physical]Data[10 03];
3. Send DiagBy[Physical]Data[19 <Sub> <DTCStatusMask>];
```

**D. 子功能不支持（负向）— Extended 会话**
```
1. Send DiagBy[Physical]Data[10 01];
2. Send DiagBy[Physical]Data[10 03];
3. Send DiagBy[Physical]Data[19 <UnsupportedSub> <DTCStatusMask>];
```

#### Check 规则（expected_output）

**A. 当前会话不支持服务（Default 会话）：**
- 第 1 步：`Check DiagData[50 01 <P2_H> <P2_L> <P2*_H> <P2*_L>]Within[50]ms;`
- 第 2 步：`Check DiagData[7F 19 7F]Within[50]ms;`

**B. 支持子功能正向（需 DTC 数据，Extended 会话）：**
- 第 1 步：`Check DiagData[50 01 <P2_H> <P2_L> <P2*_H> <P2*_L>]Within[50]ms;`
- 第 2 步：`Check DiagData[50 03 <P2_H> <P2_L> <P2*_H> <P2*_L>]Within[50]ms;`
- 第 3-4 步：不写 Check（Stop MsgCycle/Delay 为非诊断操作）
- 第 5 步按子功能区分：
  - 0x01: `Check DiagData[59 01 <AvailabilityMask> <N_DTC_H> <N_DTC_L>]Within[50]ms;`
  - 0x02: `Check DiagData[59 02 <AvailabilityMask> <DTC_H> <DTC_M> <DTC_L> <Status>]Within[50]ms;`
  - 0x04: `Check DiagData[59 04 <DTC_3bytes> <Status> <RecordNum> <SnapshotData>]Within[50]ms;`
  - 0x06: `Check DiagData[59 06 <DTC_3bytes> <Status> <RecordNum> <ExtData>]Within[50]ms;`
- 第 6 步：不写 Check（Send MsgCycle 为非诊断操作）

**C. 支持子功能正向（不需 DTC 数据，Extended 会话）：**
- 第 1 步：`Check DiagData[50 01 <P2_H> <P2_L> <P2*_H> <P2*_L>]Within[50]ms;`
- 第 2 步：`Check DiagData[50 03 <P2_H> <P2_L> <P2*_H> <P2*_L>]Within[50]ms;`
- 第 3 步：
  - 0x01: `Check DiagData[59 01 <AvailabilityMask> <N_DTC_H> <N_DTC_L>]Within[50]ms;`
  - 0x0A: `Check DiagData[59 0A <DTCStatusAvailabilityMask> <DTC_3bytes> <Status> ...]Within[50]ms;`

**D. 子功能不支持（Extended 会话）：**
- 第 1 步：`Check DiagData[50 01 <P2_H> <P2_L> <P2*_H> <P2*_L>]Within[50]ms;`
- 第 2 步：`Check DiagData[50 03 <P2_H> <P2_L> <P2*_H> <P2*_L>]Within[50]ms;`
- 第 3 步：`Check DiagData[7F 19 12]Within[50]ms;`

**注意**：非诊断操作步骤（Stop MsgCycle、Delay、Send MsgCycle）不在 Expected Output 中列出，**禁止使用 `--` 占位**。

#### 特殊规则

1. DTCStatusMask 通常使用 FF（查询所有状态位）
2. Snapshot Record Number: 01=首次故障, 02=最近故障, FF=全部
3. 扩展数据（0x06）包含: Occurrence Counter + Timestamp(Y/M/D/H/M/S) + Odometer + Voltage + Speed
4. 若 DTC 快照表为空，0x04 子功能可能返回空数据
5. 有 DTC 数据的子功能（0x02/0x04/0x06）需先制造故障再读取
6. 无 DTC 数据的子功能（0x01/0x0A）可直接读取
7. **test_procedure 中只写操作（Send/Delay/Stop/Resume），绝对禁止写 Check**
8. **步骤编号严格使用 `N. ` 格式，禁止使用 `StepN:` 格式**

---

### 分类 2: SPRMIB Test
#### 用例数量规则

- 设 `R` = 支持的会话集合
- 设 `T` = 支持的子功能集合
- **总数 = |R| × |T|**

> **关键规则**：0x19 无 Subfunction 概念，SPRMIB 不适用。但需验证发送 suppress bit（0x8x）时 ECU 的行为。
> 参考模板确认：所有 0x19 子功能发送 `0x80 + Sub` 均返回 NRC 0x12。

#### 用例命名规则

- `<SessionName> session 0x19 service does not support the suppress bit`

#### 测试步骤模板

**⚠️ test_procedure 中只写 Send 操作，步骤编号严格使用 `N. ` 格式，禁止使用 `StepN:` 格式。**

**Default 会话：**
```
1. Send DiagBy[Physical]Data[10 01];
2. Send DiagBy[Physical]Data[19 <0x80 + Sub> <DTCStatusMask>];
```

**Extended 会话：**
```
1. Send DiagBy[Physical]Data[10 01];
2. Send DiagBy[Physical]Data[10 03];
3. Send DiagBy[Physical]Data[19 <0x80 + Sub> <DTCStatusMask>];
```

例如：
- `19 81 FF`（0x01 + suppress bit）
- `19 82 FF`（0x02 + suppress bit）
- `19 8A`（0x0A + suppress bit）

#### Check 规则（expected_output）

**Default 会话：**
- 第 1 步：`Check DiagData[50 01 <P2_H> <P2_L> <P2*_H> <P2*_L>]Within[50]ms;`
- 第 2 步：`Check DiagData[7F 19 12]Within[50]ms;`

**Extended 会话：**
- 第 1 步：`Check DiagData[50 01 <P2_H> <P2_L> <P2*_H> <P2*_L>]Within[50]ms;`
- 第 2 步：`Check DiagData[50 03 <P2_H> <P2_L> <P2*_H> <P2*_L>]Within[50]ms;`
- 第 3 步：`Check DiagData[7F 19 12]Within[50]ms;`

#### 特殊规则

1. 0x19 所有子功能的 SPRMIB=N，suppress bit 不被支持
2. 发送 `0x80 + Sub` 被视为不支持的子功能，统一返回 NRC 0x12
3. 需覆盖所有支持的子功能（01/02/0A）和支持的会话

---

### 分类 3: DTC Read Function Test

#### 用例数量规则

**核心规则：为 DTC 表中每个 Support=Y 的 DTC 生成 2 条用例。**

| 状态 | 数量 | 说明 |
|------|------|------|
| t-09（故障活跃态） | N_dtc | status=0x09（bit0 testFailed=1 + bit3 confirmedDTC=1） |
| t-08（故障恢复态） | N_dtc | status=0x08（bit0 testFailed=0 + bit3 confirmedDTC=1） |

**总数 = N_dtc × 2**

其中 N_dtc = DTC 表中 Support=Y 的 DTC 数量。

> **关键规则**：每个 DTC 必须单独生成独立的故障注入+读取用例，不能合并。每个 DTC 有其特定的故障注入方法。

#### 用例命名规则

- 活跃态：`<DTCFaultDescription> t-09 state\nDTC:<DTC_Hex>`
- 恢复态：`<DTCFaultDescription> t-08 state\nDTC:<DTC_Hex>`

例如：
- `Steering wheel left zone MAT open circuit fault-09 state\nDTC:0x5D8313`
- `Steering wheel left zone MAT open circuit recovery-08 state\nDTC:0x5D8313`

#### 测试步骤模板

**⚠️ test_procedure 中只写 Send/Delay/Set/Stop/Resume 操作，绝对不要写 Check 语句！步骤编号严格使用 `N. ` 格式，禁止使用 `StepN:` 格式。**

**A. 故障活跃态（t-09）：**
```
1. Send DiagBy[Physical]Data[10 01];
2. <DTC_FaultInjection_Method>
3. Delay[<FaultActivation_Delay>]ms;
4. Send DiagBy[Physical]Data[19 02 FF];
5. Delay[<ReadInterval>]ms;
6. Send DiagBy[Physical]Data[19 02 FF];
```

**B. 故障恢复态（t-08）：**
```
1. Send DiagBy[Physical]Data[10 01];
2. <DTC_FaultInjection_Method>
3. Delay[<FaultActivation_Delay>]ms;
4. Send DiagBy[Physical]Data[19 02 FF];
5. <DTC_FaultRecovery_Method>
6. Delay[<Recovery_Delay>]ms;
7. Send DiagBy[Physical]Data[19 02 FF];
8. Delay[<ReadInterval>]ms;
9. Send DiagBy[Physical]Data[19 02 FF];
10. Send DiagBy[Physical]Data[14 FF FF FF];
11. Send DiagBy[Physical]Data[19 02 FF];
```

其中：
- `<DTC_FaultInjection_Method>` = 每个 DTC 的具体故障注入方式，从输入表 DTC 列读取
  - 电压类：`Set Voltage[7.5]V`（欠压）/ `Set Voltage[17.5]V`（过压）
  - 通讯类：`Stop SendMsg[<MsgId>]`（通讯丢失）/ `Set LIN BIT-ERROR`
- `<DTC_FaultRecovery_Method>` = 故障恢复操作
  - 电压类：`Set Voltage[13.5]V`
  - 通讯类：`Resume SendMsg[<MsgId>]`
- `<FaultActivation_Delay>` = 故障生效延时（通常 150-550ms，按 DTC 特性调整）
- `<ReadInterval>` = 读取间隔（通常 60-70ms）
- `<Recovery_Delay>` = 恢复延时（通常 150-450ms）

#### Check 规则（expected_output）

**A. 故障活跃态（t-09）：**
- 第 1 步：`Check DiagData[50 01 <P2_H> <P2_L> <P2*_H> <P2*_L>]Within[50]ms;`
- 第 2 步：不写 Check（故障注入为非诊断操作）
- 第 3 步：不写 Check（Delay 为非诊断操作）
- 第 4 步：`Check DiagData[59 02 09 00 00 00 00]Within[200]ms;`（故障尚未触发，可能返回空）
- 第 5 步：不写 Check（Delay 为非诊断操作）
- 第 6 步：`Check DiagData[59 02 09 <DTC_H> <DTC_M> <DTC_L> 09]Within[200]ms;`（故障已触发，status=0x09）

**B. 故障恢复态（t-08）：**
- 第 1 步：`Check DiagData[50 01 <P2_H> <P2_L> <P2*_H> <P2*_L>]Within[50]ms;`
- 第 2 步：不写 Check（故障注入为非诊断操作）
- 第 3 步：不写 Check（Delay 为非诊断操作）
- 第 4 步：`Check DiagData[59 02 FF <DTC_H> <DTC_M> <DTC_L> 09]Within[200]ms;`（故障活跃中）
- 第 5 步：不写 Check（故障恢复为非诊断操作）
- 第 6 步：不写 Check（Delay 为非诊断操作）
- 第 7 步：`Check DiagData[59 02 FF <DTC_H> <DTC_M> <DTC_L> 09]Within[200]ms;`（仍活跃）
- 第 8 步：不写 Check（Delay 为非诊断操作）
- 第 9 步：`Check DiagData[59 02 FF <DTC_H> <DTC_M> <DTC_L> 08]Within[200]ms;`（已恢复，status=0x08）
- 第 10 步：`Check DiagData[54]Within[200]ms;`（清除 DTC）
- 第 11 步：`Check DiagData[59 02 FF 00 00 00 00]Within[200]ms;`（清除后为空）

**注意**：非诊断操作步骤（Set Voltage、Delay、Stop SendMsg、Resume SendMsg）不在 Expected Output 中列出，**禁止使用 `--` 占位**。

#### 特殊规则

1. **每个 DTC 单独一条用例**，不可合并多个 DTC 到一条用例中
2. **同一个 DTC 号的不同故障类型**（如 LIN 通讯的 BIT-ERROR / CHECKSUM-ERROR / PARITY-ERROR）各生成独立用例
3. DTC 编号从 DTC 表读取，为 3 字节（如 `5D 83 13`）
4. 故障注入方法从 DTC 表或项目定义的故障列表中读取
5. **在 Default 会话下测试**，不切换到 Extended
6. 响应超时使用 `Within[200]ms`（比常规 50ms 更长），因为故障注入后 ECU 处理可能延迟
7. **test_procedure 中只写操作，绝对禁止写 Check；步骤编号严格使用 `N. ` 格式**

---

### 分类 4: Supply Voltage Fault Injection Test

#### 用例数量规则

**从 DTC 表提取所有电压相关 DTC（Failure Criteria 涉及电压阈值的 DTC），为每个电压 DTC 生成 2 条用例。**

| 状态 | 数量 | 说明 |
|------|------|------|
| t-09（故障活跃态） | N_voltage_dtc | status=0x09（电压故障触发后确认） |
| t-08（故障恢复态） | N_voltage_dtc | status=0x08（电压恢复后确认） |

**总数 = N_voltage_dtc × 2**

其中 N_voltage_dtc = DTC 表中 Failure Criteria 涉及电压阈值（过压/欠压）且 Support=Y 的 DTC 数量。

> **关键规则**：电压类 DTC 必须使用 `Set Voltage[...]V` 进行故障注入，不得使用其他方法替代。

#### 用例命名规则

- 活跃态：`<DTCFaultDescription> t-09 voltage fault\nDTC:<DTC_Hex>`
- 恢复态：`<DTCFaultDescription> t-08 voltage recovery\nDTC:<DTC_Hex>`

示例：
- `Power supply over voltage t-09 voltage fault\nDTC:0x800117`
- `Power supply over voltage t-08 voltage recovery\nDTC:0x800117`

#### 电压故障注入方法速查

| DTC 类型 | 故障注入方法 | 触发阈值 | 恢复方法 | 恢复阈值 |
|----------|-------------|---------|---------|---------|
| 过压（Over Voltage） | `Set Voltage[17.5]V` | ≥16.5V | `Set Voltage[13.5]V` | ≤16V |
| 欠压（Under Voltage） | `Set Voltage[7.5]V` | ≤8.5V | `Set Voltage[12.0]V` | ≥9V |

> **注意**：具体的电压 DTC 阈值以 DTC 表中 Failure Criteria 列写的数值为准。若 DTC 表中标注的阈值与上表不同，以 DTC 表为准。

#### 测试步骤模板

**⚠️ test_procedure 中只写 Send/Delay/Set 操作，绝对不要写 Check 语句！步骤编号严格使用 `N. ` 格式，禁止使用 `StepN:` 格式。**

**A. 电压故障活跃态（t-09）：**
```
1. Send DiagBy[Physical]Data[10 01];
2. Set Voltage[<FaultVoltage>]V;
3. Delay[<FaultActivation_Delay>]ms;
4. Send DiagBy[Physical]Data[19 02 FF];
5. Set Voltage[<RecoveryVoltage>]V;
6. Delay[<Recovery_Delay>]ms;
7. Send DiagBy[Physical]Data[19 02 FF];
```

**B. 电压故障恢复态（t-08）：**
```
1. Send DiagBy[Physical]Data[10 01];
2. Set Voltage[<FaultVoltage>]V;
3. Delay[<FaultActivation_Delay>]ms;
4. Send DiagBy[Physical]Data[19 02 FF];
5. Set Voltage[<RecoveryVoltage>]V;
6. Delay[<Recovery_Delay>]ms;
7. Send DiagBy[Physical]Data[19 02 FF];
8. Delay[<Aging_Delay>]ms;
9. Send DiagBy[Physical]Data[19 02 FF];
10. Send DiagBy[Physical]Data[14 FF FF FF];
11. Send DiagBy[Physical]Data[19 02 FF];
```

其中：
- `<FaultVoltage>` = 故障触发电压（过压场景用 17.5V，欠压场景用 7.5V）
- `<RecoveryVoltage>` = 正常恢复电压（通常 13.5V）
- `<FaultActivation_Delay>` = 故障生效延时（根据 DTC 表中 Monitor Rate 和故障确认周期计算）
- `<Recovery_Delay>` = 恢复延时（通常 2000ms）
- `<Aging_Delay>` = DTC 老化延时（通常 2000ms）

#### Check 规则（expected_output）

**A. 电压故障活跃态（t-09）：**
- 第 1 步：`Check DiagData[50 01 <P2_H> <P2_L> <P2*_H> <P2*_L>]Within[50]ms;`
- 第 2-3 步：不写 Check（Set Voltage/Delay 为非诊断操作）
- 第 4 步：`Check DiagData[59 02 09 <DTC_H> <DTC_M> <DTC_L> 09]Within[200]ms;`（故障已触发）
- 第 5-6 步：不写 Check（Set Voltage/Delay 为非诊断操作）
- 第 7 步：`Check DiagData[59 02 09 <DTC_H> <DTC_M> <DTC_L> 08]Within[200]ms;`（电压恢复后变为 08）

**B. 电压故障恢复态（t-08）：**
- 第 1 步：`Check DiagData[50 01 <P2_H> <P2_L> <P2*_H> <P2*_L>]Within[50]ms;`
- 第 2-3 步：不写 Check（Set Voltage/Delay 为非诊断操作）
- 第 4 步：`Check DiagData[59 02 09 <DTC_H> <DTC_M> <DTC_L> 09]Within[200]ms;`
- 第 5-6 步：不写 Check（Set Voltage/Delay 为非诊断操作）
- 第 7 步：`Check DiagData[59 02 09 <DTC_H> <DTC_M> <DTC_L> 08]Within[200]ms;`
- 第 8 步：不写 Check（Delay 为非诊断操作）
- 第 9 步：`Check DiagData[59 02 09 <DTC_H> <DTC_M> <DTC_L> 08]Within[200]ms;`（确认 DTC 仍为 08）
- 第 10 步：`Check DiagData[54]Within[200]ms;`（清除 DTC）
- 第 11 步：`Check DiagData[59 02 09 00 00 00 00]Within[200]ms;`（清除后无 DTC）

**注意**：非诊断步骤（Set Voltage、Delay）不在 Expected Output 中列出，**禁止使用 `--` 占位**。

---

### 分类 5: Supply Voltage Boundary Test

#### 用例数量规则

**固定 4 条**，覆盖电压边界场景。即使 DTC 表中无电压相关 DTC，也须生成（验证 ECU 在边界电压下的正常工作能力）。

| 序号 | 场景 | 电压值 | 预期结果 |
|------|------|--------|---------|
| 1 | 正常工作下限边界 | 9.0V | 无 DTC 触发，0x19 正常响应 |
| 2 | 欠压阈值边界 | 8.5V | DTC 触发，status=0x09 |
| 3 | 正常工作上限边界 | 16.0V | 无 DTC 触发，0x19 正常响应 |
| 4 | 过压阈值边界 | 16.5V | DTC 触发，status=0x09 |

> **注意**：若 DTC 表中实际电压阈值不同于上述默认值（8.5V/16.5V），以 DTC 表为准。边界测试的电压值 = DTC 表中 Failure Criteria 标注的阈值电压。

#### 用例命名规则

1. `Supply voltage lower boundary 9.0V no DTC`
2. `Supply voltage under-voltage threshold boundary DTC`
3. `Supply voltage upper boundary 16.0V no DTC`
4. `Supply voltage over-voltage threshold boundary DTC`

#### 测试步骤模板

**⚠️ test_procedure 中只写 Send/Delay/Set 操作，绝对不要写 Check 语句！步骤编号严格使用 `N. ` 格式，禁止使用 `StepN:` 格式。**

**A. 下限边界 — 无 DTC（9.0V）：**
```
1. Send DiagBy[Physical]Data[10 01];
2. Set Voltage[9.0]V;
3. Delay[3000]ms;
4. Send DiagBy[Physical]Data[19 02 FF];
5. Send DiagBy[Physical]Data[19 01 FF];
6. Set Voltage[13.5]V;
7. Delay[1000]ms;
```

**B. 欠压阈值边界 — 触发 DTC（8.5V）：**
```
1. Send DiagBy[Physical]Data[10 01];
2. Set Voltage[8.5]V;
3. Delay[3000]ms;
4. Send DiagBy[Physical]Data[19 02 FF];
5. Send DiagBy[Physical]Data[19 01 FF];
6. Set Voltage[13.5]V;
7. Delay[3000]ms;
8. Send DiagBy[Physical]Data[19 02 FF];
9. Send DiagBy[Physical]Data[14 FF FF FF];
```

**C. 上限边界 — 无 DTC（16.0V）：**
```
1. Send DiagBy[Physical]Data[10 01];
2. Set Voltage[16.0]V;
3. Delay[3000]ms;
4. Send DiagBy[Physical]Data[19 02 FF];
5. Send DiagBy[Physical]Data[19 01 FF];
6. Set Voltage[13.5]V;
7. Delay[1000]ms;
```

**D. 过压阈值边界 — 触发 DTC（16.5V）：**
```
1. Send DiagBy[Physical]Data[10 01];
2. Set Voltage[16.5]V;
3. Delay[3000]ms;
4. Send DiagBy[Physical]Data[19 02 FF];
5. Send DiagBy[Physical]Data[19 01 FF];
6. Set Voltage[13.5]V;
7. Delay[3000]ms;
8. Send DiagBy[Physical]Data[19 02 FF];
9. Send DiagBy[Physical]Data[14 FF FF FF];
```

#### Check 规则（expected_output）

**A. 下限边界 — 无 DTC（9.0V）：**
- 第 1 步：`Check DiagData[50 01 <P2_H> <P2_L> <P2*_H> <P2*_L>]Within[50]ms;`
- 第 2-3 步：不写 Check（Set Voltage/Delay 为非诊断操作）
- 第 4 步：`Check DiagData[59 02 09]Within[200]ms;`（仅 AvailabilityMask，无 DTC 数据）
- 第 5 步：`Check DiagData[59 01 09 00 00]Within[200]ms;`（DTC 数量为 0）
- 第 6-7 步：不写 Check（Set Voltage/Delay 为非诊断操作）

**B. 欠压阈值边界 — 触发 DTC（8.5V）：**
- 第 1 步：`Check DiagData[50 01 <P2_H> <P2_L> <P2*_H> <P2*_L>]Within[50]ms;`
- 第 2-3 步：不写 Check（Set Voltage/Delay 为非诊断操作）
- 第 4 步：`Check DiagData[59 02 09 80 01 16 09]Within[200]ms;`（欠压 DTC 已触发，DTC 编号以 DTC 表为准）
- 第 5 步：`Check DiagData[59 01 09 00 01]Within[200]ms;`（DTC 数量为 1）
- 第 6-7 步：不写 Check（Set Voltage/Delay 为非诊断操作）
- 第 8 步：`Check DiagData[59 02 09 80 01 16 08]Within[200]ms;`（电压恢复后变为 08）
- 第 9 步：`Check DiagData[54]Within[200]ms;`

**C. 上限边界 — 无 DTC（16.0V）：**
- 第 1 步：`Check DiagData[50 01 <P2_H> <P2_L> <P2*_H> <P2*_L>]Within[50]ms;`
- 第 2-3 步：不写 Check（Set Voltage/Delay 为非诊断操作）
- 第 4 步：`Check DiagData[59 02 09]Within[200]ms;`（仅 AvailabilityMask，无 DTC 数据）
- 第 5 步：`Check DiagData[59 01 09 00 00]Within[200]ms;`（DTC 数量为 0）
- 第 6-7 步：不写 Check（Set Voltage/Delay 为非诊断操作）

**D. 过压阈值边界 — 触发 DTC（16.5V）：**
- 第 1 步：`Check DiagData[50 01 <P2_H> <P2_L> <P2*_H> <P2*_L>]Within[50]ms;`
- 第 2-3 步：不写 Check（Set Voltage/Delay 为非诊断操作）
- 第 4 步：`Check DiagData[59 02 09 80 01 17 09]Within[200]ms;`（过压 DTC 已触发，DTC 编号以 DTC 表为准）
- 第 5 步：`Check DiagData[59 01 09 00 01]Within[200]ms;`（DTC 数量为 1）
- 第 6-7 步：不写 Check（Set Voltage/Delay 为非诊断操作）
- 第 8 步：`Check DiagData[59 02 09 80 01 17 08]Within[200]ms;`（电压恢复后变为 08）
- 第 9 步：`Check DiagData[54]Within[200]ms;`

**注意**：非诊断步骤（Set Voltage、Delay）不在 Expected Output 中列出，**禁止使用 `--` 占位**。

#### 特殊规则

1. **边界测试的电压值优先从 DTC 表读取**，若 DTC 表无明确阈值则使用默认值（9.0V / 8.5V / 16.0V / 16.5V）
2. 非诊断步骤（Set Voltage、Delay）**不在 Expected Output 中列出**，**禁止使用 `--` 占位**
3. DTC 编号以 DTC 表中对应电压故障的实际 DTC 号为准
4. 0x19 01 用于验证 DTC 数量，0x19 02 用于验证具体 DTC 状态
5. 边界测试完成后必须恢复电压到正常值（13.5V）并清除 DTC

---

### 分类 6: Incorrect Diagnostic Command Test
#### 用例数量规则

**固定 2 条 / 每种支持的寻址方式**

| 序号 | 错误类型 | 描述 |
|------|---------|------|
| 1 | SF_DL > 合法值 | 有效负载长度大于合法值 |
| 2 | SF_DL < 合法值 | 有效负载长度小于合法值 |

> **注意**：客户当前参考模板中 **不包含 DLC 错误测试**（DLC < 8 / DLC > 8），只测 SF_DL 异常。

#### 用例命名规则

1. `Valid SF_DL=<legal>, invalid SF_DL > <legal>, and those with invalid equivalence class SF_DL=<value> NegativeCase-$19`
2. `Valid SF_DL=<legal>, invalid SF_DL < <legal>, and those with invalid equivalence class SF_DL=<value> NegativeCase-$19`

其中 `<legal>` 随子功能变化：0x01/0x02/0x0A=2

#### 测试步骤模板

**⚠️ test_procedure 中只写 Send 操作，绝对不要写 Check 语句！步骤编号严格使用 `N. ` 格式，禁止使用 `StepN:` 格式。**

选择一个代表性子功能（优先 0x01）进行测试。

**Extended Session — SF_DL > 合法值**
```
1. Send DiagBy[Physical]Data[10 01];
2. Send DiagBy[Physical]Data[10 03];
3. Send DiagBy[Physical]Data[19 01]WithLen[5];
```

**Extended Session — SF_DL < 合法值**
```
1. Send DiagBy[Physical]Data[10 01];
2. Send DiagBy[Physical]Data[10 03];
3. Send DiagBy[Physical]Data[19 01]WithLen[1];
```

#### Check 规则（expected_output）

**SF_DL > 合法值：**
- 第 1 步：`Check DiagData[50 01 <P2_H> <P2_L> <P2*_H> <P2*_L>]Within[50]ms;`
- 第 2 步：`Check DiagData[50 03 <P2_H> <P2_L> <P2*_H> <P2*_L>]Within[50]ms;`
- 第 3 步：`Check DiagData[7F 19 13]Within[50]ms;`

**SF_DL < 合法值：**
- 第 1 步：`Check DiagData[50 01 <P2_H> <P2_L> <P2*_H> <P2*_L>]Within[50]ms;`
- 第 2 步：`Check DiagData[50 03 <P2_H> <P2_L> <P2*_H> <P2*_L>]Within[50]ms;`
- 第 3 步：`Check DiagData[7F 19 13]Within[50]ms;`

---

### 分类 7: Functional Addressing Test

#### 用例数量规则

**无论参数表 `Functional Request` 为何值，都生成完整的 Functional 寻址用例集。**

- 复制 Session Layer Test 中所有正向用例（支持的子功能 × 支持的会话 × DTCStatusMask）
- 再加上 Incorrect Diagnostic Command 的 Functional 版
- **总数 = Session Layer 正向数 + Incorrect 数**

#### 用例命名规则

沿用 Session Layer 命名，发送寻址方式改为 `[Function]`/`[Funcation]`

#### 测试步骤模板

与 Session Layer 相同，但 `[Physical]` 改为 `[Function]`/`[Funcation]`

#### Check 规则

**当 `Functional Request = N` 时：**
- 所有 Functional 用例统一：`Check No_Response Within[1000]ms;`

**当 `Functional Request = Y` 时：**
- 与 Physical 相同的 Check 规则

#### 特殊规则

1. 即使 Functional Request=N，仍需为所有支持的子功能×会话生成 Functional 用例
2. Case ID 中 `Phy` 改为 `Fun`，编号继续 Phy 编号递增
3. Incorrect Command 的 Functional 版也需生成

---

## 会话进入标准路径

见共享文件。0x19 无额外覆盖规则。

---

## 生成注意事项

> 通用规则（Case ID 不可重复、pipe table 格式、`<br>` 换行、每 Send 有 Check 等）见共享文件。

1. **编号从 001 开始**，优先编写所有 Physical 用例，Functional 编号继续递增
2. **DTC 编号格式为 3 字节**（如 5D 83 13），从 DTC 表读取
3. **Session Layer 须测试多个 DTCStatusMask**（FF / 0x08 / 0x09），来自 GroupOfDTC 支持的 bit 位
4. **不同子功能的合法 SF_DL 不同**，Incorrect Command 测试需标注合法值
5. **DTC Read 必须按逐 DTC 生成**，每个 DTC 生成 t-09 活跃态 + t-08 恢复态各 1 条
6. **电压类 DTC 必须用 Set Voltage[...]V 进行故障注入**，不得用其他方法替代（分类 4）
7. **电压边界测试固定 4 条**，覆盖 9V/8.5V/16V/16.5V 四个边界点（分类 5）
8. **Functional 寻址无论是否支持都必须生成全套用例**
9. **非诊断操作步骤（Set Voltage、Delay、Stop SendMsg 等）不在 Expected Output 中列出**，**禁止使用 `--` 占位**

### 分类 8: NRC Priority Test
#### 用例数量规则

**固定 1 条 / 每个软件域 / 物理寻址**

> 根据输入表 NRC 优先级链（如 `0x13>0x12>0x31`），只生成 1 条验证最高优先级 NRC 的用例。

#### 用例命名规则

`NRC <NRC_Priority_Chain>`

例如：`NRC 13>12>31`

#### 测试步骤模板

**⚠️ test_procedure 中只写 Send 操作，步骤编号严格使用 `N. ` 格式，禁止使用 `StepN:` 格式。**

```
1. Send DiagBy[Physical]Data[10 01];
2. Send DiagBy[Physical]Data[10 03];
3. Send DiagBy[Physical]Data[19 <UnsupportedSub> <Data>]WithLen[<InvalidLen>];
```

构造方法：选择不支持的子功能（触发 NRC 0x12），同时设置非法长度（触发 NRC 0x13），ECU 应返回优先级最高的 NRC 0x13。

#### Check 规则（expected_output）

- 第 1 步：`Check DiagData[50 01 <P2_H> <P2_L> <P2*_H> <P2*_L>]Within[50]ms;`
- 第 2 步：`Check DiagData[50 03 <P2_H> <P2_L> <P2*_H> <P2*_L>]Within[50]ms;`
- 第 3 步：`Check DiagData[7F 19 13]Within[50]ms;`（返回优先级最高的 NRC）

#### 特殊规则

1. 只生成 1 条，不需要为每个 NRC 组合都生成
2. 验证的核心：当多个 NRC 条件同时满足时，ECU 返回优先级最高的那个

---

## 分类总览

0x19 固定 9 类生成能力（按顺序）：

| 分类 | 名称 | 说明 |
|------|------|------|
| 1 | Session Layer Test | 多 DTCStatusMask（FF/0x08/0x09）× 子功能 × 会话 |
| 2 | SPRMIB Test | 验证 suppress bit 返回 NRC 0x12 |
| 3 | DTC Read Function Test | 逐 DTC 生成，每个 DTC 2 条（t-09 + t-08） |
| 4 | Supply Voltage Fault Injection Test | 电压 DTC 专项故障注入，每个电压 DTC 2 条（t-09 + t-08） |
| 5 | Supply Voltage Boundary Test | 固定 4 条，验证电压边界（9V/8.5V/16V/16.5V）DTC 行为 |
| 6 | Incorrect Diagnostic Command Test | 固定 2 条（仅 SF_DL 异常） |
| 7 | Functional Addressing Test | 无论 Functional Request 是否支持都生成全套 |
| 8 | NRC Priority Test | 固定 1 条/域/Physical |
| 9 | Boot Domain Test | Boot 域独立生成（若存在 0x19 数据） |

生成条数由以下因素共同决定：
- 支持的子功能集合
- 支持的会话集合
- DTCStatusMask 组合
- DTC 列表（Support=Y 的每个 DTC 各 2 条）
- 电压 DTC 数量（每个电压 DTC 2 条）
- 电压边界测试（固定 4 条）
- 软件域（App / BootLoader）
- Functional Request 状态
