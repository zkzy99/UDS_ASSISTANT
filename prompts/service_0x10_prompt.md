## 0.1 输入字段读取口径（只针对 0x10 ）

#### `1.Basic Diagnostic Infomation`
用于生成公共参数：

- `Diagnostic Req CANID(only for CAN ECU)`：物理寻址错误帧测试使用
- `Diagnostic Functional Req CANID(only for CAN ECU)`：功能寻址错误帧测试使用
- `P2Server Max`：0x10 正响应中的 `P2Server_max`
- `P2*Server Max`：0x10 正响应中的 `P2*Server_max`
- `S3Server`：0x10 S3 超时测试使用
- `$11 Timing parameters -> reset_time Support / Byte Length / Unit`：0x11 正响应是否带 `resetTime` 参数

#### `2.Diagnostic Services`
用于生成 0x10 用例矩阵：

- `Service ID`
- `Service Name`
- `Subfunction`
- `Subfunction Name`
- `Hex Value`
- `Support`
- `SPRMIB`
- `Physical Request`
- `Functional Request`
- `Supported Session in App`
  - `Default 0x01`
  - `Programming 0x02`
  - `Extended 0x03`
  - `Access Level`
- `Supported Session in BootLoader`
  - `Default 0x01`
  - `Programming 0x02`
  - `Extended 0x03`
  - `Access Level`
- `Negative response codes`
只参考一个service id：

- `DiagnosticSessionControl_0x10`

生成结果重点字段：

- **D 列**：用例名称样式（Default Session to  Default Session PositiveCase-$10；Default Session to  Programming Session NegativeCase-$10）
- **I 列**：测试步骤写法（Send DiagBy[Physics]Data[10 01];Send DiagBy[Physics]Data[10 01];）
- **J 列**：预期输出写法（1.Check DiagData[50 01 00 32 00 C8]Within[50]ms;2.Check DiagData[50 01 00 32 00 C8]Within[50]ms;）

汽车电子函数接口定义：
用于确定 CAPL 风格函数接口的标准写法：

- `Send DiagBy[Physical]Data[...]`
- `Send DiagBy[Function]Data[...]`
- `Send Msg[...]Data[...]WithDLC[...]`
- `Check DiagData[...]Within[...]ms`
- `Check No_Response Within[...]ms`
- `Send Security Right KeyBy[...]Level[...]`
- `Send SubTraversalBy[...]Service[...]Excluding[...]AndCheckResp[...]`
- `Send DiagBy[...]Data[...]WithLen[...]`
- `Check MsgInexist[...]`
- `Check MsgExist[...]`

---

## 0.2 整体结构要求

每个软件域（App / Boot）每种寻址方式（Physical / Functional）必须独立生成完整用例集。

生成顺序：
1. **App Physical** — 标题 `1.Application Service_Physical Addressing`
2. **App Functional** — 标题 `2.Application Service_Functional Addressing`（仅当 Functional=Y）
3. **Boot Physical** — 标题 `3.Boot Service_Physical Addressing`
4. **Boot Functional** — 标题 `4.Boot Service_Functional Addressing`（仅当 Functional=Y）

每组内部按固定顺序包含 8 类测试。每组 Case ID 独立递增（Phy 从 001 开始，Fun 从 001 开始）。

---

## 0.2.1 输出格式要求

1. **输出格式严格为 pipe table**，列顺序：`| Case ID | Case名称 | 测试步骤 | 预期输出 |`
2. **步骤中换行使用 `<br>` 标记**，不用 `\n`
3. **不要生成任何"参数提取结果"或"分析"段落**，直接输出测试用例表格
4. **NRC 优先级链从参数表精确读取**，不要猜测

## 0.2.2 Timing 参数提取规则

从参数表精确提取：
- P2 Server Max → 直接读取 ms 值，hex 编码公式：`P2ms / 1` → 转为 2 字节 hex
- P2* Server Max → hex 编码公式：`P2*ms / 10` → 转为 2 字节 hex
- 示例：P2=50ms → 50=0x0032 → `00 32`；P2*=5000ms → 500=0x01F4 → `01 F4`
- 0x10 正响应格式：`50 <Sub> <P2_H> <P2_L> <P2*_H> <P2*_L>`

---

## 0.2.3 输出格式通用规则

### 0.2.1 Case ID 规则

统一采用：

- 物理寻址：`Diag_0x10_Phy_001`、`Diag_0x11_Phy_001`
- 功能寻址：`Diag_0x10_Fun_001`、`Diag_0x11_Fun_001`

规则：

- `Diag_`
- 服务号（如 `0x10`）
- 寻址方式（`Phy` / `Fun`）
- 三位流水号

### 0.2.2 Case 名称规则

#### 0x10
- Session：`Service 0x10 <CurrentSession> To <TargetSession>`
- SPRMIB：`Service 0x10 <CurrentSession> To <TargetSession> with SPRMIB`
- Secure Access：`Security access Lx unlock supports jumping to <TargetSession> Session`
- ECU Reset：`ECU <ResetType> reset Session returns to the Default Session`
- Traversal：`Subfunction traversal test in the <CurrentSession> Session`
- S3：`S3Server maintains...` / `S3Server returns...`
- Incorrect Command：`When a diagnostic message with DLC != 8` / `Valid SF_DL=2, invalid SF_DL != 2`

#### 0x11
- Session：`Service 0x11 <CurrentSession> supports/nonsupport <SubfunctionName>`
- SPRMIB：在 Session 名称后加 `with SPRMIB`
- Secure Access：`Security access Lx unlock supports 0x11 service <Subfunction>`
- Reset Effect：`0x11 Service <Subfunction> <ResetEffect>`
- Traversal：`Subfunction traversal test in the <CurrentSession> Session`
- Incorrect Command / Functional：`When a diagnostic message with DLC != 8` / `Valid SF_DL=2, invalid SF_DL != 2`

### 0.2.3 测试步骤与预期输出的编写原则

1. **每一个发送动作原则上都要有对应 check（Expected Output）。**
2. **以下两类步骤不单独写 Expected Output：**
   - `Delay[...]ms`
   - 已带 `AndCheckResp[...]` 的发送函数
3. **以下检查型步骤本身就是检查动作，不再在 Expected Output 中重复：**
   - `Check MsgInexist[...]`
   - `Check MsgExist[...]`
4. `Check DiagData[...]Within[50]ms` 为默认诊断响应检查写法。
5. `Check No_Response Within[1000]ms` 为默认“无响应”检查写法；若业务明确指定更长时间，按客户规则覆盖。
6. 0x10 正响应格式：
   - `50 <Subfunction> <P2ServerMax_H> <P2ServerMax_L> <P2*ServerMax_H> <P2*ServerMax_L>`
   - `50 serviceID 0x10 + 0x40`
7. 0x11 正响应格式：
   - 若 `reset_time Support = N`：`51 <Subfunction>`
   - 若 `reset_time Support = Y`：`51 <Subfunction> <ResetTime_H> <ResetTime_L>`
   - `51 serviceID 0x11 + 0x40`

---

## 0.3 协议与报文通用规则

### 0.3.1 0x10 正/负响应规则

- 正响应：`<service ID +40> + Subfunction + timing parameter`
- 负响应：`7F <service ID> <NRC>`

典型 NRC：

- `0x12`：Subfunction Not Supported
- `0x13`：Incorrect Message Length Or Invalid Format
- `0x22`：Conditions Not Correct
- `0x7E`：Subfunction Not Supported In Active Session

**NRC 优先级链（服务级，0x10 专用）**：

| 优先级 | NRC | 触发条件 |
|--------|-----|---------|
| 1 | 0x13 | 长度错误（SF_DL≠2） |
| 2 | 0x12 | 子功能不支持 |
| 3 | 0x7E | 子功能在当前会话不支持 |
| 4 | 0x22 | 前提条件不满足（如进入 Programming 前置条件） |

### 0.3.2 0x11 正/负响应规则

- 正响应：`<service ID +40> + Subfunction [+ resetTime]`
- 负响应：`7F <service ID> <NRC>`

典型 NRC：

- `0x12`：Subfunction Not Supported
- `0x13`：Incorrect Message Length Or Invalid Format
- `0x22`：Conditions Not Correct
- `0x7E`：Subfunction Not Supported In Active Session
- `0x7F`：Service Not Supported In Active Session（客户模板中用于“当前会话下整体不支持 0x11 服务”的口径）

### 0.3.3 SPRMIB 规则

- 子功能抑制位：`0x80 + 原子功能`
- 对 **执行成功** 的请求：
  - 若支持 SPRMIB，则 **抑制肯定响应**，检查 `No_Response`
- 对 **执行失败** 的请求：
  - 仍返回 **否定响应**

> **NRC 0x78（Response Pending）注意**：若项目中 ECU 在处理请求时可能先回 `NRC 0x78`（Request Correctly Received - Response Pending），则 SPRMIB 的 `No_Response` 检查需要排除 0x78：
> - 收到 `7F <SID> 78` 说明请求已被接收且处理中，不应视为"无响应"
> - 此时应等待最终响应（正响应或最终负响应），再判断是否满足 SPRMIB 抑制预期
> - 根据项目实际情况决定是否需要特殊处理 0x78 场景


### 0.3.4 0x10 进入会话的标准准备路径

为了让自动生成器输出稳定、便于评审，进入当前会话建议统一使用如下规范路径：

- 进入 Default：`10 01`
- 进入 Extended：`10 01 -> Delay[1000]ms -> 10 03`
- 进入 Programming：`10 01 -> Delay[1000]ms -> 10 03 -> 31 01 02 03 -> 10 02`

> **重要**：进入 Programming 会话前必须先执行 RoutineControl（如 `31 01 02 03`），否则 ECU 可能拒绝进入 Programming。
> 说明：这不是 ISO 唯一允许路径，沉淀出来的”标准建链路径”，便于统一生成。

**退出路径规则**：若前置路径经过了 Programming 会话（`10 02`），再切回 Default（`10 01`）后，**必须插入 `Delay[1000]ms`**，等 ECU 完成会话切换后再执行下一步诊断请求。这是因为在 Programming 会话中 ECU 可能执行了内部状态变更，切回 Default 后需要时间完成清理。

### 0.3.5 安全访问解锁的标准写法

先根据 0x10 所在域读取 `Access Level`，再到 0x27 中取对应的 seed/key 对：

- `L2` 对应：`27 03 / 27 04`
- `L4` 对应：`27 07 / 27 08`
- 其他等级：按输入表Service ID 0x27 行映射，不写死

统一写法：

1. 先进入允许发种子的会话
2. `Send DiagBy[Physical]Data[27 <SeedSub>]AndCheckResp[PositiveResponse]`
3. `Send Security Right KeyBy[Physical]Level[<KeySub>]`
4. 再发送被测服务请求

> 说明：**安全访问步骤本身统一使用物理寻址**；只有被测 0x10 会话切换请求在功能寻址类 case 中改成 Function。

---

# 1. Service 0x10 DiagnosticSessionControl (8 类测试)

## 1.0 适用范围

0x10 的分类框架按 PDF 固定为 8 类：

1.1 Session Layer Test
1.2 SPRMIB Test
1.3 Secure Access Test
1.4 ECU Reset Test
1.5 Sub-function Traversal Test
1.6 S3 Server Timer Test
1.7 Incorrect Diagnostic Command Test
1.8 NRC Priority Test

### 寻址方式规则

若 `Functional Request` 支持，则在相同软件域下 **额外生成一份 Functional 寻址用例**；
若 `Functional Request` 不支持，则不生成 Functional 版。

> **注意**：Functional 寻址不是简单的 Physical 1:1 复制。部分类别的数量和行为在 Functional 下不同：
> - **S3 Timer**：Physical 2 条 vs Functional 2 条
> - **Incorrect Command**：Physical 2 条 vs Functional 2 条（数量相同但用不同 CAN ID）
> - **NRC Priority**：Physical 和 Functional 均生成（Functional 下 NRC 0x12 预期改为 No_Response）
> - **ECU Reset**：Physical 和 Functional 都生成，但 reset 触发和验证步骤统一用 Physical

### 软件域规则

**必须独立为每个软件域生成完整用例集。** 软件域按输入表区分：

- Application / App
- BootLoader / Boot / FBL

若输入表中同时包含 `ApplicationServices` 和 `BootServices` 两个 Sheet（或同一 Sheet 中包含 App 和 Boot 两段数据），则 **必须为两个域分别生成完整的 8 类测试用例**。两个域的子功能支持矩阵、会话权限、安全等级可能完全不同，不能复用。

> **示例**：若输入有 App 域（3 个子功能）和 Boot 域（3 个子功能），且 Physical 和 Functional 都支持，则生成结构为：
> ```
> 1. App Physical: 8 类用例
> 2. App Functional: 8 类用例（NRC Priority 中 NRC 0x12 预期改为 No_Response）
> 3. Boot Physical: 8 类用例
> 4. Boot Functional: 8 类用例（NRC Priority 中 NRC 0x12 预期改为 No_Response）
> ```

---

## 1.1 Session Layer Test


### 1.1.1 用例数量规则

**通用公式：**

- 设 `R` = 当前软件域下可达的“当前会话集合”
- 设 `T` = 当前软件域下 0x10 支持的目标子功能集合（01/02/03）
- 则 **Session Layer Test 数量 = `|R| × |T|`**

#### 最少条数
- **1 条**
- 场景：只有 `10 01` 被支持，且只验证 Default -> Default

#### 最多条数
- **9 条 / 每个软件域 / 每种支持的寻址方式**
- 场景：`01/02/03` 全支持，且 Default / Extended / Programming 都可作为当前会话

### 1.1.2 用例命名规则

`Service 0x10 <CurrentSessionName> To <TargetSessionName>`

例如：

- `Service 0x10 Default To Default`
- `Service 0x10 Extended To Programming`
- `Service 0x10 Programming To Extended`

### 1.1.3 测试步骤模板

#### A. 正向类（目标子功能在当前会话下允许）

**步骤模板：**

1. 进入 `<CurrentSession>`
2. 发送 `Send DiagBy[<Addr>]Data[10 <TargetSub>]`

其中：

- `<Addr>` = `Physical` 或 `Function`
- `<TargetSub>` ∈ `01 / 02 / 03`

**当前会话进入步骤建议：**

- Current = Default  
  `1.Send DiagBy[<Addr>]Data[10 01];`

- Current = Extended  
  `1.Send DiagBy[<Addr>]Data[10 01];`  
  `2.Delay[1000]ms;`  
  `3.Send DiagBy[<Addr>]Data[10 03];`

- Current = Programming
  `1.Send DiagBy[<Addr>]Data[10 01];`
  `2.Delay[1000]ms;`
  `3.Send DiagBy[<Addr>]Data[10 03];`
  `4.Send DiagBy[<Addr>]Data[31 01 02 03];`
  `5.Send DiagBy[<Addr>]Data[10 02];`

然后再发：

- `5.Send DiagBy[<Addr>]Data[10 <TargetSub>];`

### 1.1.4 Check 规则

#### 进入当前会话的 check
- `10 01` -> `Check DiagData[50 01 <P2> <P2*>]Within[50]ms;`
- `10 03` -> `Check DiagData[50 03 <P2> <P2*>]Within[50]ms;`
- `10 02` -> `Check DiagData[50 02 <P2> <P2*>]Within[50]ms;`

其中：

- `<P2>` = 从 `P2Server Max` 转换成 2 字节十六进制
- `<P2*>` = 从 `P2*Server Max / 10` 转换成 2 字节十六进制

#### 目标请求的 check
- 若允许切换：`Check DiagData[50 <TargetSub> <P2> <P2*>]Within[50]ms;`
- 若目标子功能在该当前会话下不支持：`Check DiagData[7F 10 7E]Within[50]ms;`
- 若目标子功能因前置条件不满足（例如编程会话前置条件未满足）：`Check DiagData[7F 10 22]Within[50]ms;`

### 1.1.5 特殊规则

1. **全局不支持的子功能** 不在 Session Layer 里出用例，而是放到 `1.5 Sub-function Traversal Test`。
2. 功能寻址版的 0x10 Session Layer，**原则上和物理寻址预期一致，只改发送寻址方式**。
3. **功能寻址 NRC 0x12 屏蔽规则**：若 ECU 本应返回 NRC 0x12（Subfunction Not Supported），在功能寻址下该 NRC **被屏蔽**，ECU 不回复，预期为 `Check No_Response Within[1000]ms;`。其他 NRC（如 0x7E、0x22、0x13）在功能寻址下仍正常返回对应负响应。

---

## 1.2 SPRMIB Test


### 1.2.1 用例数量规则

**通用公式：**

- 设 `R` = 当前软件域可达的当前会话集合
- 设 `T` = 当前软件域 0x10 所有支持的子功能集合（**不区分 SPRMIB 是否支持**）
- 则 **SPRMIB Test 数量 = `|R| × |T|`**

> **关键规则**：SPRMIB 测试必须覆盖 **所有子功能**，不仅仅是 `SPRMIB=Y` 的子功能。
> - `SPRMIB=Y` 的子功能：发送 `0x80 + Sub`，预期响应被抑制（No_Response）
> - `SPRMIB=N` 的子功能：发送 `0x80 + Sub`，此时 suppress bit 不被支持，ECU 可能按原子功能处理或返回 NRC；按输入表 `Negative response codes` 判定预期响应

#### 最少条数
- **0 条**
- 场景：该服务没有任何支持的子功能

#### 最多条数
- **9 条 / 每个软件域 / 每种支持的寻址方式**
- 即 `3 个当前会话 × 3 个子功能 = 9 条`

### 1.2.2 用例命名规则

`Service 0x10 <CurrentSessionName> To <TargetSessionName> with SPRMIB`

### 1.2.3 测试步骤模板

在 Session Layer 的同名 case 基础上，把最终请求改为：

- `10 <0x80 + TargetSub>`

例如：

- `10 01` -> `10 81`
- `10 02` -> `10 82`
- `10 03` -> `10 83`

### 1.2.4 Check 规则

- 若原始请求应为正向执行成功：
  - `Check No_Response Within[1000]ms;`
  - **追加验证**：SPRMIB 抑制成功后，需追加一步验证会话状态是否确实发生了切换：
    - 若目标会话支持 31 服务：`Send DiagBy[Physical]Data[31 01 02 03];` + 对应 check
    - 若目标会话不支持 31 服务：通过 27 服务或其他可用服务验证
  - 示例（SPRMIB 抑制从 Extended 切到 Default 后验证仍在 Default）：
    - `Check No_Response Within[1000]ms;`
    - `Send DiagBy[Physical]Data[31 01 02 03];` → `Check DiagData[7F 31 7F]Within[50]ms;`
- 若原始请求本应为负向：
  - 仍检查对应 NRC
  - 会话不支持：`7F 10 7E`
  - 前置条件不满足：`7F 10 22`
  - 其他非法子功能：`7F 10 12`

### 1.2.5 特殊规则

1. `No_Response` 只适用于 **成功且支持 SPRMIB 的场景**。
2. `Delay` 不写 check。
3. 带 `AndCheckResp[...]` 的步骤不再单列 Expected Output。
4. 若客户后续明确某一特定寻址方式“负向也统一无响应”，则再做客户化覆盖；当前规则不默认这样做。

---

## 1.3 Secure Access Test


### 1.3.1 用例数量规则

**通用公式：**

- 设 `Tu` = 需要先解锁才能进入/验证的目标会话集合
- 则 **Secure Access Test 数量 = `|Tu|`**

#### 最少条数
- **0 条**
- 场景：该软件域下 0x10 不受安全等级限制

#### 最多条数
- **3 条 / 每个软件域 / 每种支持的寻址方式**
- 对应跳转到 `Default / Programming / Extended`

### 1.3.2 用例命名规则

`Security access Lx unlock supports jumping to <TargetSessionName> Session`

### 1.3.3 测试步骤模板

1. 进入允许安全访问 seed 请求的当前会话
2. `Send DiagBy[Physical]Data[27 <SeedSub>]AndCheckResp[PositiveResponse];`
3. `Send Security Right KeyBy[Physical]Level[<KeySub>];`
4. `Send DiagBy[<Addr>]Data[10 <TargetSub>];`

#### 推荐前置会话
- App/L2：先入 `10 03`
- Boot/L4：先入 `10 02` 或按 0x27 规则进入编程会话后再发种子

### 1.3.4 Check 规则

- 进入前置会话：检查 `50 03...` 或 `50 02...`
- 第 2 步不单独写 Expected Output（因 `AndCheckResp` 已内含检查）
- 第 3 步：`Check DiagData[67 <KeySub>]Within[50]ms;`
- 第 4 步：
  - 成功切换：`Check DiagData[50 <TargetSub> <P2> <P2*>]Within[50]ms;`
  - 若解锁后仍不允许：按输入表 `Negative response codes` 字段取值检查

### 1.3.5 特殊规则

1. 安全等级 **不写死成 L2**，必须从输入表当前软件域 `Access Level` 读取。
2. 如果某目标会话本身不支持，则不生成对应 Secure Access case。
3. 功能寻址类 0x10 Secure Access 用例中，**0x27 种子/密钥过程仍使用 Physical**；只有被测 `10 xx` 改成 `Function`。

---

## 1.4 ECU Reset Test

### 1.4.1 用例数量规则

**通用公式：**

- 固定包含：`Power Reset` 1 条
- 再加：0x11 中 **Support=Y** 的子功能类型 `Nreset11`
- 则 **ECU Reset Test 数量 = `1 + Nreset11`**

> **关键规则**：只为 0x11 中 **实际支持（Support=Y）** 的子功能生成 reset 用例。不支持的子功能无需测试，因为 reset 请求本身会被 ECU 拒绝，无法验证 0x10 会话状态。

#### 最少条数
- **1 条**
- 只有电源重启验证

#### 最多条数
- **4 条**
- 典型场景：`Power Reset + HardReset + KeyOffOnReset + SoftReset`

> 当前客户模板显式落了 `Power Reset / Hardware Reset / Software Reset` 三类（KeyOffOn 视项目而定）。

### 1.4.2 用例命名规则

`ECU <ResetType> reset Session returns to the Default Session`

### 1.4.3 测试步骤模板

#### A. Power Reset
1. 进入非默认会话（App 域建议 `10 03`；Boot 域建议 `10 02`）
2. `Set Voltage[0]V;`
3. `Delay[3000]ms;`
4. `Set Voltage[12]V;`
5. `Delay[3000]ms;`
6. 验证会话回到 Default（见 1.4.4 Check 规则）

#### B. 0x11 Hardware / Soft / KeyOffOn Reset
1. 进入非默认会话（App 域建议 `10 03`；Boot 域建议 `10 02`）
2. `Send DiagBy[Physical]Data[11 <ResetSub>];`
3. `Delay[1000]ms;`
4. 验证会话回到 Default（见 1.4.4 Check 规则）

### 1.4.4 Check 规则

- 第 1 步进入非默认会话：`Check DiagData[50 03 ...]Within[50]ms;`（App 域）或 `Check DiagData[50 02 ...]Within[50]ms;`（Boot 域）
- 0x11 reset 请求：
  - `11 01` -> `Check DiagData[51 01]Within[50]ms;`
  - `11 02` -> `Check DiagData[51 02 ...]Within[50]ms;`（若支持）
  - `11 03` -> `Check DiagData[51 03]Within[50]ms;`
- reset 后验证会话回到 Default（按优先级选择验证方式）：
  1. 若支持 DID F186：`Send DiagBy[Physical]Data[22 F1 86];` → `Check DiagData[62 F1 86 01]Within[50]ms;`
  2. 若不支持 F186：通过 31 服务验证 — `Send DiagBy[Physical]Data[31 01 02 03];` → `Check DiagData[7F 31 7F]Within[50]ms;`
  3. 或通过 27 服务验证（根据项目实际情况选择）

### 1.4.5 特殊规则

1. **Power Reset 为客户强制保留项。**
2. 用例目的不是验证 0x11 自身，而是验证 **0x10 所在状态在 reset 后回到 Default**。
3. 功能寻址版 0x10 的 Reset Test 中：
   - 进入非默认会话的 `10 xx` 可用 `Function`
   - 复位触发与复位后验证仍使用 `Physical`

---

## 1.5 Sub-function Traversal Test


### 1.5.1 用例数量规则

**通用公式：**

- 设 `A` = 需要覆盖的当前会话锚点集合
- 则 **Traversal 用例数 = `|A|`**

#### 最少条数
- **1 条**

#### 最多条数
- **3 条**
- 覆盖 `Default / Extended / Programming` 三种当前会话语义

### 1.5.2 用例命名规则

`Subfunction traversal test in the <CurrentSessionName> Session`

### 1.5.3 测试步骤模板

1. 进入 `<CurrentSession>`
2. `Send SubTraversalBy[<Addr>]Service[0x10]Excluding[<SupportSubList>]AndCheckResp[<RespCode>];`

其中：

- `<SupportSubList>` = 当前软件域下所有支持的 0x10 子功能 + 对应支持的 SPRMIB 子功能
  - 例如：`01 02 03 81 82 83`
- `<RespCode>` 通常取 `0x12`

### 1.5.4 Check 规则

- 第 1 步：检查进入当前会话的正响应
- 第 2 步：**不单独写 Expected Output**
  - 因为 `AndCheckResp[<RespCode>]` 已内嵌检查

### 1.5.5 特殊规则

1. 这里遍历的是 **“除支持列表以外”的全部子功能**。
2. 若当前会话下服务有效，但遍历到的子功能全局不支持，预期 `0x12`。
3. 不要把本应在 Session Layer 中验证的“支持但当前会话不允许”的目标子功能混到 traversal 中。

---

## 1.6 S3 Server Timer Test

### 1.6.1 用例数量规则

**通用公式：**

- **物理寻址**：**2 条**（S3 未超时会话保持 + S3 超时返回 Default）
- **功能寻址**：**2 条**（S3 未超时会话保持 + S3 超时返回 Default）

> **关键规则**：物理寻址和功能寻址的 S3 用例数量一致，均需覆盖"保持"和"超时返回 Default"两种场景。

### 1.6.2 用例命名规则

- `S3Server maintains the Session without timeout`
- `S3Server returns to the default Session upon timeout`

### 1.6.3 测试步骤模板

#### A. 未超时
1. 进入 Default
2. 进入 Extended（或其它非默认会话）
3. `Delay[<S3 - delta>]ms;`
4. `Send DiagBy[Physical]Data[22 F1 86];`

#### B. 已超时
1. 进入 Default
2. 进入 Extended（或其它非默认会话）
3. `Delay[<S3 + delta>]ms;`
4. `Send DiagBy[Physical]Data[22 F1 86];`

其中：

- `<S3>` 来自 `S3Server`
- `delta` 建议至少 100ms，避免边界抖动

### 1.6.4 Check 规则

**会话状态验证方式**（按优先级选择）：
1. 若支持 DID F186：`Send DiagBy[Physical]Data[22 F1 86];` → 检查返回的会话值
2. 若不支持 F186：通过 31 服务验证 — `Send DiagBy[Physical]Data[31 01 02 03];`
   - 在非默认会话：`Check DiagData[71 01 02 03 00]Within[50]ms;`
   - 在 Default 会话：`Check DiagData[7F 31 7F]Within[50]ms;`

- 未超时（验证仍在非默认会话）：
  - 方式 1：`Check DiagData[62 F1 86 03]Within[50]ms;`
  - 方式 2：`Check DiagData[71 01 02 03 00]Within[50]ms;`
- 已超时（验证回到 Default 会话）：
  - 方式 1：`Check DiagData[62 F1 86 01]Within[50]ms;`
  - 方式 2：`Check DiagData[7F 31 7F]Within[50]ms;`

### 1.6.5 特殊规则

1. S3 必须验证最终会话状态（通过 DID F186 或 31 服务）；不要只看是否能继续发请求。
2. **物理寻址和功能寻址均生成 2 条**（未超时保持 + 超时返回 Default）。
3. 功能寻址版中：
   - 会话切换用 `Function`
   - S3 超时后的状态确认仍推荐用 `Physical`

---

## 1.7 Incorrect Diagnostic Command Test


### 1.7.1 用例数量规则

**通用公式：**

- **固定 2 条 / 每种支持的寻址方式**

两类错误：

1. SF_DL > 合法长度（如 `SF_DL=3`，合法为 2）
2. SF_DL < 合法长度（如 `SF_DL=1`，合法为 2）

> **注意**：客户当前参考模板中 **不包含 DLC 错误测试**（DLC < 8 / DLC > 8），只测 SF_DL 异常。
> 若项目后续明确要求增加 DLC 错误帧测试，可扩展为 4 条。

### 1.7.2 用例命名规则

沿用 PDF 原文：

- `When a diagnostic message with DLC < 8 is sent, ECU does not respond`
- `When a diagnostic message with DLC > 8 is sent, ECU responds normally`
- `Valid SF_DL=2, invalid SF_DL > 2...`
- `Valid SF_DL=2, invalid SF_DL < 2...`

### 1.7.3 测试步骤模板

#### A. SF_DL > 2
`Send DiagBy[<Addr>]Data[10 01]WithLen[3];`

#### B. SF_DL < 2
`Send DiagBy[<Addr>]Data[10 01]WithLen[1];`

### 1.7.4 Check 规则

- SF_DL > 2：
  - `Check DiagData[7F 10 13]Within[50]ms;`
- SF_DL < 2：
  - `Check DiagData[7F 10 13]Within[50]ms;`

### 1.7.5 特殊规则

1. 0x10 的合法 SF_DL 为 **2 字节数据负载**（SID + Subfunction）。
2. SF_DL 错误测试使用 `Send DiagBy...WithLen[...]`。
3. 测试前需先进入 Default Session 建立诊断会话。

---

## 1.8 NRC Priority Test


### 1.8.1 用例数量规则

- **NRC 优先级链中相邻 NRC 对的数量 / 每个软件域 / 物理寻址 + 功能寻址**

> 物理寻址和功能寻址均生成 NRC Priority 用例。
> 每个相邻 NRC 对生成 1 条用例，验证高优先级 NRC 优先于低优先级 NRC 返回。
> 功能寻址下 NRC 0x12 被屏蔽，预期为 `Check No_Response`；其他 NRC 正常返回。

例如优先级链 `13>12>7E>22` 有 3 对，生成 3 条：
- 验证 `13(min Size) > 12`：SF_DL 不满足最小长度 + 不支持子功能
- 验证 `12 > 13(no min size)`：SF_DL > 2 但子功能不支持
- 验证 `7E > 22`：在当前会话不支持该子功能时请求

若项目有车速等前置条件限制，额外生成 1 条前置条件验证用例。

### 1.8.2 用例命名规则

**NRC 优先级：**
`NRC <NRC_Priority_Chain>` — 例如 `NRC 13(min Size)>12`、`NRC 12>13(no min size)`

**前置条件：**
`When the preset speed condition is not met, NRC: 0x22 is reported`

其中 NRC 优先级链来自输入表的 `Negative response codes` 字段，按优先级排列。

### 1.8.3 测试步骤模板

**目标**：验证 NRC 优先级链中每一对相邻 NRC 的优先级关系。

以优先级链 `13>12>7E>22` 为例，生成 3 条用例：

**用例 1：验证 `13(min Size) > 12`**
1. 进入 Default Session
2. `Send Msg[<ReqCANID>]Data[01 10 <UnsupportedSub>]WithDLC[8];`（SF_DL=1，不满足最小长度 + 不支持子功能）
3. 预期（物理寻址）：`Check DiagData[7F 10 13]Within[50]ms;`
4. 预期（功能寻址）：`Check DiagData[7F 10 13]Within[50]ms;`（NRC 0x13 不被屏蔽）

**用例 2：验证 `12 > 13(no min size)`**
1. 进入 Default Session
2. `Send Msg[<ReqCANID>]Data[03 10 <UnsupportedSub>]WithDLC[8];`（SF_DL=3，满足最小长度但子功能不支持）
3. 预期（物理寻址）：`Check DiagData[7F 10 12]Within[50]ms;`
4. 预期（功能寻址）：`Check No_Response Within[1000]ms;`（NRC 0x12 被功能寻址屏蔽）

**用例 3：验证 `7E > 22`**
1. 进入 Default Session（Programming 未解锁，不满足前置条件）
2. `Send DiagBy[<Addr>]Data[10 02];`（支持的子功能，但当前会话不支持 + 前置条件不满足）
3. 预期：`Check DiagData[7F 10 7E]Within[50]ms;`

**前置条件验证（车速示例，若项目有此限制）**
1. 进入 Default Session
2. `Change MsgID[<SpeedMsg>]Data[<ZeroSpeedData>]CycleTime[100]ms;`
3. `Send Msg[<ReqCANID>]Data[02 10 <RepSub>]WithDLC[8];`
4. 预期：`Check DiagData[7F 10 22]Within[50]ms;`

### 1.8.4 Check 规则

- 每条用例验证一对相邻 NRC 的优先级关系
- 同时触发两个 NRC 条件时，ECU 应返回优先级更高的 NRC

### 1.8.5 特殊规则

1. NRC 优先级顺序来自输入表的 `Negative response codes` 字段（如 `13>12>7E>22`）。
2. 该测试验证的是 ECU 的 NRC 仲裁逻辑，不是单一条件。
3. 如果输入表未给出 NRC 优先级链，则跳过本类测试。
4. 优先级链中有 N 对相邻 NRC，就生成 N 条用例。
5. **物理寻址和功能寻址均生成 NRC Priority 用例**；功能寻址下 NRC 0x12 预期改为 `No_Response`。
6. 若项目有车速等前置条件限制，额外生成前置条件 NRC 0x22 验证用例。

---

> **注意**：0x11 (ECUReset) 的规则已迁移至独立文件 `prompts/service_0x11_prompt.md`。
> 本文件仅包含 0x10 (DiagnosticSessionControl) 的规则。

---

## 生成注意事项

1. **不可省略任何分类**，8 类必须全部生成（条件不满足的标明"无符合条件的用例"）
2. **Boot 域也必须生成 Functional 用例**（当 Functional=Y 时）
3. **不要生成任何"参数提取结果"或"分析"段落**，直接输出测试用例表格
4. **输出格式严格为 pipe table**，列顺序：`| Case ID | Case名称 | 测试步骤 | 预期输出 |`
5. **步骤中换行使用 `<br>` 标记**，不用 `\n`
6. **NRC 优先级链从参数表精确读取**，不要猜测
