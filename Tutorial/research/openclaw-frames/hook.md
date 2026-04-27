OpenClaw 里的 **hook**，主要作用是：**让外部系统用 HTTP webhook 的方式把事件送进 Gateway，然后让 OpenClaw 记一条系统事件、唤醒 heartbeat，或者启动一次 agent 任务。**

它可以理解成 OpenClaw 的“外部事件入口”。

比如：

- Gmail 来了一封邮件，Google Pub/Sub 推到 `/hooks/gmail`
- GitHub、Mattermost、Slack、你自己的服务发一个 webhook 到 `/hooks/xxx`
- 外部脚本想让 OpenClaw “现在醒一下”
- 外部系统想直接触发某个 agent 处理一段消息

OpenClaw 里主要有三个 hook 入口：

```text
POST /hooks/wake
POST /hooks/agent
POST /hooks/<name>
```

`/hooks/wake` 的作用比较轻：把一段文本作为 system event 放进主 session，然后按 `mode` 决定是否立刻唤醒 heartbeat。

请求类似：

```json
{
  "text": "Gmail has a new message",
  "mode": "now"
}
```

`mode` 可以是：

```text
now
next-heartbeat
```

`now` 就是马上叫醒；`next-heartbeat` 是先记录事件，等下一次心跳再处理。

`/hooks/agent` 更重一些：它会启动一次 agent run。请求类似：

```json
{
  "message": "Summarize this webhook payload",
  "name": "Gmail",
  "agentId": "hooks",
  "sessionKey": "hook:gmail:xxx",
  "wakeMode": "now",
  "deliver": true,
  "channel": "last"
}
```

它不是简单记录事件，而是会创建一个类似 cron isolated agent turn 的任务，让 agent 去处理这条消息。源码里可以看到它构造了一个 `CronJob`，然后调用 `runCronIsolatedAgentTurn`。

`/hooks/<name>` 是映射型 webhook，例如：

```text
POST /hooks/gmail
POST /hooks/github
POST /hooks/some-service
```

它会根据配置里的 `hooks.mappings` 匹配路径，然后把外部 payload 转成 OpenClaw 内部 action：

```json5
{
  match: { path: "gmail" },
  action: "agent",
  agentId: "hooks",
  wakeMode: "now",
  messageTemplate: "From: {{messages[0].from}}\nSubject: {{messages[0].subject}}",
  deliver: true
}
```

所以 `/hooks/gmail` 收到外部 JSON 后，可以被模板/transform 转成一条 agent 消息。

它的通信方式是 **HTTP POST + JSON**，本质是 webhook，不是 WebSocket，也不是 SSE。

和 `/tools/invoke` 的区别：

```text
/hooks/*
外部事件入口：告诉 OpenClaw “发生了什么”，让它 wake 或启动 agent。

/tools/invoke
直接调用某个 OpenClaw tool，拿 tool result。
```

安全上，hook 有自己单独的 token，不应该复用 gateway token。OpenClaw 支持：

```text
Authorization: Bearer <hooks.token>
x-openclaw-token: <hooks.token>
```

并且明确不允许把 token 放 query string 里。它还有一些限制项，比如：

- `allowedAgentIds`：限制 hook 能调哪些 agent
- `defaultSessionKey`：hook 默认写入哪个 session
- `allowRequestSessionKey`：是否允许请求自己指定 sessionKey，默认 false
- `allowedSessionKeyPrefixes`：限制 hook 生成的 sessionKey 前缀
- `maxBodyBytes`：限制 payload 大小
- idempotency key：防止重复 webhook 重复触发

一句话总结：

**OpenClaw 的 hook 是外部系统接入 OpenClaw 自动化的入口。它把“外部事件”转换成 OpenClaw 的 system event、heartbeat wake，或者一次 agent run。**