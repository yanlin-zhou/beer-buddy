# 使用与安装

版本 1.2.1 · 文档更新日期：2026-10-15；安装入口来源核对日期：2026-10-14。

## 只想先试一下

打开 [START.md](../START.md)，复制代码框全文到一个新的 AI 对话，再说你的场景，例如：

> 这瓶是 Happy Hops IPA，介绍一下，讲点有意思的，也告诉我喝哪里可以留意。

能看图的对话里，也可以直接拍单款酒。辨认清楚后，默认给这款或酒厂的小故事，再加一个品饮观察，通常三四句；查不到可靠的相关故事时直说，不编来历。只问怎么喝、只讲故事或只问服务操作，仍按你的明确要求回答。

发酒单时可以说：“帮我从几个不同角度挑挑看。”清楚的酒单默认给 3–5 款、通常 3 或 4 款备选，每款一个有依据的理由；明确只要一杯，就直接收敛。

这版带菜单规则与示例事实、单杯故事与品饮指导和 4 条故事。需要完整 14 条故事、更多品饮入口与选酒、采购参考时，下载 [PROMPT.md](https://github.com/yanlin-zhou/beer-buddy/releases/latest/download/PROMPT.md)，上传到支持文本附件的对话，发：“请按文件中的啤酒搭子帮我。”

也可复制完整文件到容量足够的对话。不要默认任何平台的“自定义指令”都容得下整份资料。平台是否能读附件、看图或联网，以你的当前账户和模型为准；本项目不需要 API key，也没有额外服务。

## Claude Code

在终端执行：

```bash
git clone https://github.com/yanlin-zhou/beer-buddy.git ~/.claude/skills/beer-buddy
```

打开一个新会话，输入：

```text
/beer-buddy 这瓶是 Happy Hops IPA，简单介绍一下。
```

若目录已存在，`git clone` 会停止。不要覆盖或删除自己的改动；如果该目录就是这个仓库的 Git 克隆，可先检查 `git status`，确认无自己的未提交改动后，再在该目录执行 `git pull --ff-only`。

这是 Claude Code 本地安装路径。Claude 网页端和 Cowork 的安装入口不同，不由这个目录自动同步。[Claude Code 官方 Skills 文档](https://code.claude.com/docs/en/skills)

## Codex

个人 Skill 可放在 `~/.agents/skills/`：

```bash
git clone https://github.com/yanlin-zhou/beer-buddy.git ~/.agents/skills/beer-buddy
```

新建或重新打开会话后说：

```text
用 $beer-buddy 介绍我眼前这杯，讲点有意思的，再说一个喝时能留意的地方。
```

Codex 通常会自动检测 Skill 变化；没出现时重启会话或应用。已存在同名目录时停止安装，先检查原有版本，避免重复目录造成两个同名 Skill。不要把本地修改直接覆盖掉。[Codex 官方 Skills 文档](https://learn.chatgpt.com/docs/build-skills)

## Claude 自定义 Skill 上传

下载 Release 中的 [beer-buddy-1.2.1.zip](https://github.com/yanlin-zhou/beer-buddy/releases/download/v1.2.1/beer-buddy-1.2.1.zip)。它包含顶层 `beer-buddy/` 文件夹，里面直接有 `SKILL.md`。

在支持自定义 Skills 的 Claude 界面中，进入 **Customize → Skills → + → Create skill → Upload a skill** 上传。不同产品、账户权限或更新可能改变入口；以 [Claude 官方上传说明](https://support.claude.com/en/articles/12512180-use-skills-in-claude)及当前界面为准。

使用专门的 Release 安装包，别将 GitHub 自动生成的源码包误当成专用安装包。各宿主实际验证范围见[验证记录](VALIDATION.md)。

## 装完试这几句

1. 发一张清楚的酒单：`帮我看看，给几个不同理由的选择。` —— 资料足够时，应给几款不同候选，理由具体，不先问一串偏好题。
2. 同一张酒单：`只选一杯，十秒内，想清爽。` —— 应缩到一款和必要理由。
3. `这瓶是 Happy Hops IPA，介绍一下，让我知道喝哪里有意思。` —— 应有这款或酒厂的小故事，以及一个可留意的点；普通风味知识不能顶替故事。
4. `这杯只说怎么喝，故事我知道了。` —— 应只给一个观察与必要解释，不重复历史。
5. `我只觉得苦，只给一句，别编其他味道。` —— 应保留你的感受。
6. `今天结束了，只记录：我更喜欢小麦。` —— 应只记录，不追加下一杯。

想听故事时，直接说“只给一个故事，不要品酒教程”，新版本也会尊重这次的要求。

如果单款泛介绍仍只有品饮没有故事，也未说明缺少依据；菜单资料充足却只给一款；或要求你喝出某个味道、先问一串问题，先确认启用的是 v1.2.1。把**提示词与实际回答**提交到 [Issue](https://github.com/yanlin-zhou/beer-buddy/issues)，即可帮助我们排查；不要贴私人对话和凭据。

## 这次实际验证到哪里

[验证记录](VALIDATION.md)分别列出文件与打包检查、Agent 文本测试、宿主实测和真人验证。安装路径参考官方文档，不能等同于每个平台都已实装成功。
