对，你的理解没错：**SSE 最常见的用途就是服务端持续流式输出**，比如模型 token、日志、进度、事件通知。

OpenClaw 里 `session_history` 用 SSE，不是为了“生成式 token 流式输出”，而是为了做 **会话历史的实时订阅**。

也就是说这个接口有两种模式：

```text
GET /sessions/{sessionKey}/history
```

普通请求时：返回一次性的历史 JSON。

```text
Accept: text/event-stream
```

时：先返回当前历史，然后连接不断开，后面有新消息就继续推送。

OpenClaw 的逻辑大概是：

```text
1. 客户端打开 /sessions/main/history，Accept: text/event-stream
2. 服务端先发 event: history，把当前历史发过去
3. 后续 transcript 有新消息
4. 服务端继续发 event: message
5. 客户端 UI 不需要轮询，就能实时更新
```

所以它不是 LLM token streaming，而是 **session transcript streaming**。

大概像这样：

```text
event: history
data: {"sessionKey":"main","messages":[...]}

event: message
data: {"sessionKey":"main","message":{...}}
```

为什么不用 WebSocket？OpenClaw 其实也有 WebSocket 主控制面，里面有：

```text
session.message
sessions.changed
chat
agent
```

但 HTTP SSE 有几个好处：

1. 浏览器接入简单  
   前端可以直接用：

```js
new EventSource("/sessions/main/history")
```

2. 只需要服务端到客户端单向推送  
   history 订阅只需要“服务端推新消息”，客户端不需要在这条连接里发命令。SSE 刚好适合。

3. 比轮询轻  
   不用每隔 1 秒 `GET /history` 一次。

4. 比 WebSocket 更轻量  
   不需要维护双向协议、request id、method、event envelope。

所以可以理解成：

```text
chat token streaming 也可以用 SSE
session history 实时更新也可以用 SSE
日志 tail / 任务进度 / 通知事件 也都可以用 SSE
```

SSE 的本质不是“只能流式 token”，而是：

```text
HTTP 上的服务端单向事件流
```

OpenClaw 在这里用它，是为了让会话历史页面或轻量客户端可以实时收到新 transcript。