# 乐享开发规范

## 1. 背景

本文从**编程、安全、数据库、中间件、单元测试、异常日志、结构分层**几个维度给出最小必要规范。
每条规范尽量采用“**说明 + 正例 + 反例**”形式，便于落地和复用。

## 2. 编程规约

### 2.1 类注释规约

说明：类注释应帮助新人快速理解职责与版本信息，禁止保留 IDE 默认模板。

正例：

```java
/**
 * 【一级特性】【二级特性】
 *
 * @author 姓名
 * @date 2023-06-14 12:00
 * @version 1.4.0
 */
```

反例：直接使用 IDE 默认模板，如 `${DESCRIPTION}`、`${USER}` 等占位符未替换。

### 2.2 方法注释规约

说明：方法注释应便于 `smart-doc` 生成接口文档。

要求：
- `remark`：概括方法用途。
- `@apiNote`：补充详细说明。
- `@param` / `@return`：描述清晰、具体，不得照搬模板。

正例：

```java
/**
 * 替换已有资产结果
 *
 * @param ciId 资产id
 * @param execId 执行id
 * @param mainResId 主资源id
 * @param account 用户|张三
 * @apiNote 详细描述
 * @return 替换结果
 */
```

反例：直接保留 IDE 自动生成的 `#foreach` 模板内容。

### 2.3 属性注释规约（Bean）

说明：属性注释应明确字段含义、示例值和是否必填。

正例：

```java
/**
 * 关系类型：0-创建，1-更新，2-删除
 * @mock 示例值
 * @required
 */
```

### 2.4 避免 NPE 规约

#### 基本原则

- 【强制】POJO 属性使用**包装类型**。
- 【强制】RPC 入参与返回值使用**包装类型**。
- 【推荐】局部变量优先使用**基本类型**。
- 【强制】前后端列表接口无数据时返回空数组 `[]` 或空集合 `{}`。
- 【推荐】方法允许返回 `null` 时，必须在注释中明确说明场景。

#### 常见风险点

- 基本类型接收可能为 `null` 的值时触发自动拆箱 NPE。
- 数据库查询结果、远程调用返回值、Session 数据都可能为 `null`。
- `obj.getA().getB().getC()` 级联调用容易 NPE。
- `ConcurrentHashMap` **不允许** `null` key/value。
- `new BigDecimal(null)` 会抛异常。
- `Collection#addAll(null)` 会抛异常。
- `Collectors.toMap()` 在 value 为 `null` 时可能抛 NPE。
- 三目运算符两侧类型对齐时，可能因自动拆箱导致 NPE。

#### 推荐做法

- 使用 `Optional`、`Assert`、非空注解（如 `javax.validation`）提升空安全。
- 对不确定类型的对象先做 `instanceof` 判断，谨慎强转。
- 可使用 Apache Commons Collections4 / Guava 等空安全工具库。

正例：

```java
List<String> list = null;
if (CollectionUtils.isNotEmpty(list)) {
	// 安全处理
}
```

反例：

```java
Integer a = 1;
Integer b = 2;
Integer c = null;
Boolean flag = false;

// a * b 为 int，c 会被强制拆箱，触发 NPE
Integer result = flag ? a * b : c;
```

### 2.5 线程使用规约

说明：优先使用线程池，不要直接 `new Thread()`。

正例：使用 `ThreadPoolTaskExecutor` 统一管理线程、队列、拒绝策略和异常处理。

反例：

```java
new Thread(() -> {
	// do something
}).start();
```

## 3. 安全规约

### 3.1 待补充

当前章节保留，后续可补充鉴权、敏感信息脱敏、SQL 注入防护等内容。

## 4. 数据库规约

### 4.1 PostgreSQL

#### 4.1.1 `IN` 条件禁止重复参数

说明：`IN` 子句出现重复参数会影响执行计划与查询性能，压测环境已复现。

正例：先对参数去重，再执行查询。

```sql
SELECT *
FROM tb_alert
WHERE main_ci_id IN ('id1', 'id2', 'id3')
  AND state IN ('0', '1', '2')
ORDER BY create_time DESC, id DESC
LIMIT 20 OFFSET 0;
```

反例：

```sql
SELECT *
FROM tb_alert
WHERE main_ci_id IN ('id1', 'id2', 'id3', 'id3', 'id3')
  AND state IN ('0', '1', '2', '2');
```

结论：参数重复可能导致索引无法被正常利用，性能显著下降。

#### 4.1.2 建表必须有主键

说明：主键用于保证数据完整性、提升检索效率、支撑外键关系和表关联。

正例：

```sql
CREATE TABLE insight.tb_model_backup (
	id varchar NOT NULL,
	task_id varchar NOT NULL,
	model_code varchar NOT NULL,
	"type" varchar NOT NULL,
	table_name varchar NOT NULL,
	db_name varchar NOT NULL,
	in_time timestamp NOT NULL,
	update_time timestamp NULL,
	db_schema varchar,
	db_type varchar NOT NULL,
	CONSTRAINT tb_model_backup_pkey PRIMARY KEY (id)
);
```

反例：建表不设置主键。

#### 4.1.3 跨领域建表归属

说明：多个模块同时依赖新表时，由**先升级部署的模块**负责建表。

正例：`ccs` 与 `appserver` 同时依赖某表，若 `ccs` 先升级，则由 `ccs` 建表。

反例：`ccs` 先升级，但表创建放在 `appserver`，导致升级失败。

### 4.2 ClickHouse

### 4.3 ArangoDB

以上章节暂未补充具体规约，保留结构即可。

## 5. 中间件规约

### 5.1 MQ 创建规约

说明：消息队列应由**发送方创建**；跨领域场景下，由**先升级的一方**创建。

正例：手动注册，或使用注解：`@RabbitListener(queuesToDeclare = @Queue(QUEUE_AUTO_CONFIG))`

## 6. 单元测试规约

### 6.1 待补充

当前章节保留，后续可补充测试覆盖、断言规范、Mock 使用边界等内容。

## 7. 异常与日志规约

### 7.1 异常规范

#### 7.1.1 不要通过 `catch` 处理可预检查的运行时异常

说明：如 `NullPointerException`、`IndexOutOfBoundsException` 等，应通过前置判断规避；无法预检查的场景（如数字解析）除外。

正例：

```java
if (obj != null) {
	obj.method();
}
```

反例：

```java
try {
	obj.method();
} catch (NullPointerException e) {
	// 不推荐
}
```

#### 7.1.2 异常不要用于流程控制

说明：异常用于处理意外情况，不应用于替代条件判断。

#### 7.1.3 `catch` 要区分异常类型

说明：不要对大段非稳定代码统一 `try-catch`；应按异常类型分别处理，便于定位和恢复。

正例：注册场景中，对非法字符、用户名重复、弱密码分别提示。

### 7.2 日志规范

#### 7.2.1 统一使用 SLF4J 门面

说明：禁止直接依赖 Log4j、Logback API。

```java
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

private static final Logger logger = LoggerFactory.getLogger(Abc.class);
```

#### 7.2.2 低级别日志必须使用占位符或条件输出

说明：避免无效字符串拼接和对象 `toString()` 带来的性能损耗。

正例：

```java
logger.debug("Processing trade with id: {} and symbol: {}", id, symbol);
```

或：

```java
if (logger.isDebugEnabled()) {
	logger.debug("Processing trade with id: " + id + " and symbol: " + symbol);
}
```

反例：直接使用字符串拼接输出 `debug/info` 日志。

#### 7.2.3 控制日志级别与日志量

- 生产环境禁止输出 `debug`。
- `info` 有选择地记录。
- `warn` 可用于记录用户输入错误，但要控制日志量。
- `error` 仅用于系统逻辑错误、异常等重要问题。

记录日志前建议先问自己：
- 这条日志真的有人看吗？
- 它能帮助排障吗？
- 它会不会制造噪音？

## 8. 结构分层规约

### 8.1 待补充

当前章节保留，后续可补充分层职责、依赖方向、DTO/VO/DO 边界等内容。
