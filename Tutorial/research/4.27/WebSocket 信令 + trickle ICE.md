**WebSocket 信令 + trickle ICE** 可以拆开看。

**1. WebSocket 信令**

WebRTC 本身只负责音视频传输，不规定“双方怎么交换连接信息”。

所以 client 和 server 需要先交换这些东西：

```text
offer
answer
ICE candidate
```

这一步叫 **信令 signaling**。

我们现在用 WebSocket 做信令通道：

```text
浏览器  <--- WebSocket /ws --->  aiohttp server
```

浏览器先发：

```json
{
  "type": "offer",
  "description": {
    "type": "offer",
    "sdp": "..."
  }
}
```

服务端用 aiortc 生成 answer，再回：

```json
{
  "type": "answer",
  "description": {
    "type": "answer",
    "sdp": "..."
  }
}
```

之后双方就可以开始尝试建立 WebRTC 连接。

**2. ICE 是什么**

ICE 可以理解为 WebRTC 找路的过程。

因为两端可能在：

```text
同一台机器
同一个局域网
不同 NAT 后面
公司网络
公网
```

WebRTC 需要找到一条能打通的网络路径。每一种可能的地址/端口组合，就是一个 **ICE candidate**。

比如：

```text
本机地址 candidate
局域网地址 candidate
STUN 探测出来的公网映射 candidate
TURN 中继 candidate
```

**3. trickle ICE 是什么**

旧方式是：

```text
等所有 candidate 都收集完
一次性把 offer 发给服务端
```

这个叫 non-trickle ICE。简单，但慢。

trickle ICE 是：

```text
先发 offer
candidate 收集到一个就发一个
边收集边连接
```

所以流程变成：

```text
浏览器 -> 服务端：offer
浏览器 -> 服务端：candidate 1
浏览器 -> 服务端：candidate 2
浏览器 -> 服务端：candidate 3
服务端 -> 浏览器：answer
WebRTC 开始尝试连通
```

这样服务端会更早收到连接请求，也更早打印日志。

**4. 为什么用 WebSocket**

因为 ICE candidate 不是只发一次，可能陆续产生很多个。

用 HTTP `POST /offer` 可以交换一次 offer/answer，但不适合持续来回发 candidate。

WebSocket 很适合这种信令：

```text
连接保持打开
双方都可以随时发消息
candidate 出现就立刻发送
```

**一句话总结**

```text
WebSocket 信令 = 用 WebSocket 交换 WebRTC 连接信息
trickle ICE = ICE candidate 不等收集完，边产生边发送
```

它们配合起来的好处是：

```text
启动更快
日志更早出现
连接建立过程更接近真实生产用法
```