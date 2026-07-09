# wuxia-demo

[中文](#中文) | [English](#english)

---

## 中文

这是一个用于演示 `novel-agent` 项目结构的武侠悬疑小说样例。

## 示例流程

```bash
novel-agent plan-scenes examples/wuxia-demo --chapter 1
novel-agent write-scene examples/wuxia-demo --chapter 1 --scene 1
novel-agent write-scene examples/wuxia-demo --chapter 1 --scene 2
novel-agent compose-chapter examples/wuxia-demo --chapter 1
novel-agent summarize examples/wuxia-demo --chapter 1
novel-agent continuity examples/wuxia-demo --chapter 1
```

如果已经启用多 Agent 与向量记忆，也可以运行：

```bash
novel-agent index-memory examples/wuxia-demo
novel-agent agent-run examples/wuxia-demo --chapter 1 --goal "失忆剑客在雪夜发现第一条旧案线索"
```

---

## English

This is a wuxia mystery sample project that demonstrates the `novel-agent` project layout.

## Example flow

```bash
novel-agent plan-scenes examples/wuxia-demo --chapter 1
novel-agent write-scene examples/wuxia-demo --chapter 1 --scene 1
novel-agent write-scene examples/wuxia-demo --chapter 1 --scene 2
novel-agent compose-chapter examples/wuxia-demo --chapter 1
novel-agent summarize examples/wuxia-demo --chapter 1
novel-agent continuity examples/wuxia-demo --chapter 1
```

With multi-agent and vector memory enabled, you can also run:

```bash
novel-agent index-memory examples/wuxia-demo
novel-agent agent-run examples/wuxia-demo --chapter 1 --goal "The amnesiac swordsman finds the first old-case clue on a snowy night"
```
