---
rule_version: "1"
id: business-lab.question-ladder
---

# Business mainline question ladder

这套问题适合人在“想不出业务主线”时使用。它保留了八问的顺序，但把容易混在一起的概念拆开。技能一次只问一个问题；`不知道` 是合法答案。

## Adaptive escalation

Use the smallest intervention that keeps the user moving:

1. Ask an open micro-question.
2. If the answer is blank or vague, offer 2-4 memory-aid options.
3. If the user still cannot choose, give one sentence frame with one blank.
4. Stop and let the user write or draw. Never select an option on the user's behalf.
5. After the user produces three or more cards, ask them to reorder or rewrite the mainline before another question.

## 第 0 步：先选一个真实案例

不要从“整个系统是做什么的”开始。先选最近发生过的一次具体事情：

```text
A 新建/上传
B 修改/重命名/移动
C 删除/撤销
D 查询/下载/查看
E 分享/授权
F 审批/拒绝
G 支付/退款
H 其他
I 不知道，先给我一个场景模板
```

如果用户选 `I`，只给这个句子让他填一个空：

```text
当 ______ 想要 ______ 时，他/她先 ______。
```

## 八个问题

| 顺序 | 精确提问 | 记录什么 | 避免跳到 |
| --- | --- | --- | --- |
| 1 | 这一次事情里，谁发起、谁执行、谁受益、谁有权批准或拒绝？事情作用在什么业务对象上？ | 参与者、责任、权限、业务对象；允许一个人承担多个角色 | 把“文件/订单/用户”直接叫主角并开始建实体 |
| 2 | 什么真实业务事件让这一次事情开始？ | 触发事件和发生时间 | URL、按钮、接口、定时任务 |
| 3 | 什么结果才算这一次事情完成？谁能确认完成？ | 业务承诺、完成标准、确认者 | 页面跳转或数据库写入 |
| 4 | 从开始到完成，哪些业务变化必须发生，少一步就不成立？ | 只保留不可跳过的业务里程碑 | 把所有页面操作都列进主线 |
| 5 | 每个里程碑由谁做什么决定或动作？ | `actor + action/decision + object` | 把“系统处理”当成没有责任的黑盒 |
| 6 | 每一步之后，业务世界发生了什么变化？ | 业务事件、状态、等待条件 | 先定义状态枚举或表字段 |
| 7 | 哪一步改变了业务价值、承诺或重要信息？ | 金钱、额度、权利、归属、可见性、业务记录 | 直接回答“哪张表、哪个 Redis key” |
| 8 | 哪一步可能被拒绝、过期、重复、撤销、重试、补偿或需要人工判断？ | 分支、失败规则、责任和后果 | 只列异常名词，不说明谁处理、结果是什么 |

## 追问规则

- 用户每回答一次，先复述一句：“我记录为……，对吗？哪个词要改？”确认后才建立卡片。
- 如果答案是“用户/系统/数据”，要求补一个动词和一个业务结果。
- 如果答案是“正常/完成/失败”，要求补可观察的业务变化和确认人。
- 如果答案涉及技术词，先追问它在业务上代表的承诺或变化，再把技术词放进 `pending`。
- 如果一条主线超过九个里程碑，先问哪些可以合并；不要自动拆成更多组件或服务。
- 如果两个角色或两个词的含义不同，保留两张卡并标记冲突，不能替用户合并。

## 通过标准

一条可进入 DDD 设计的主线至少要有：一个具体案例、明确触发、业务完成标准、5-9 个不可跳过的业务变化、每步责任人、一个已命名的失败或等待分支，以及对应证据。缺一项就保持 `draft` 或 `pending`。
