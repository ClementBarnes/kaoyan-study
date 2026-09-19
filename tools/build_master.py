# -*- coding: utf-8 -*-
"""生成 单词总表.html（词根组网格式 + 相邻批次配色不同 + 跨批去重合并）。
数据：依据 单词总表.txt，把跨批重复词根合并到首现批次，共34个合并词根族。
"""
import io, os
from future_batches import FUTURE

# 调色板：20 个批次各一色，相邻批次颜色必不同
COLORS = {
    "b01": "#2563eb", "b02": "#dc2626", "b03": "#16a34a", "b04": "#d97706",
    "b05": "#7c3aed", "b06": "#0891b2", "b07": "#db2777", "b08": "#65a30d",
    "b09": "#ea580c", "b10": "#4338ca",
    "b11": "#0e7490", "b12": "#be123c", "b13": "#15803d", "b14": "#b45309",
    "b15": "#6d28d9", "b16": "#0284c7", "b17": "#c026d3", "b18": "#4d7c0f",
    "b19": "#9a3412", "b20": "#1e40af",
}

# 数据：每批 -> 根 -> (rt标签, 含义, 钩子, [(词,音标,词性释义,结构拆解,例句英,例句中)])
B = [
 {"bid":"b01","label":"第01批 (08-04) · 27词","roots":[
   {"rt":"词根 ① -spect / -spic","mean":"看（look / see）",
    "hook":"spec → 联想「spectator 观众（看比赛的人）」，核心就是“看”。",
    "words":[
     ("inspect","/ɪnˈspekt/","v. 检查，视察","in- 向内 + spect 看 → 往里看 → 检查","The manager will inspect the factory.","经理将视察工厂。"),
     ("respect","/rɪˈspekt/","v./n. 尊重","re- 回 + spect 看 → 回头看重 → 尊重","We should respect the elderly.","我们应尊重老人。"),
     ("expect","/ɪkˈspekt/","v. 期待，预期","ex- 向外 + spect 看 → 向外望 → 期待","I expect a call from him.","我等他的电话。"),
     ("aspect","/ˈæspekt/","n. 方面，外观","a- 朝向 + spect 看 → 看过去的样子 → 面貌/方面","This is only one aspect of the problem.","这只是问题的一个方面。"),
     ("prospect","/ˈprɒspekt/","n. 前景，展望","pro- 向前 + spect 看 → 向前看 → 前景","The prospect of promotion excited him.","升职的前景令他兴奋。"),
     ("perspective","/pəˈspektɪv/","n. 观点，视角","per- 贯穿 + spect 看 → 看透 → 视角","From my perspective, it is wrong.","依我看，这是错的。")]},
   {"rt":"词根 ② -port","mean":"拿 / 运 / 带（carry / bring）",
    "hook":"port → 联想「passport 护照（带在身上的通关证件）」「airport 机场/港口」，核心是“搬运/携带”。",
    "words":[
     ("import","/ˈɪmpɔːt/","v./n. 进口","im- 进 + port 运 → 运进来 → 进口","We import oil from abroad.","我们从国外进口石油。"),
     ("export","/ˈekspɔːt/","v./n. 出口","ex- 出 + port 运 → 运出去 → 出口","We export goods to Europe.","我们向欧洲出口商品。"),
     ("transport","/trænsˈpɔːt/","v./n. 运输","trans- 跨越 + port 运 → 运送","Public transport is convenient.","公共交通很方便。"),
     ("report","/rɪˈpɔːt/","v./n. 报告","re- 回 + port 带 → 带回来 → 汇报","He reported the news to his boss.","他向老板汇报了消息。"),
     ("support","/səˈpɔːt/","v./n. 支持","sup- 在下 + port 托 → 从下托住 → 支持","Her family supports her decision.","家人支持她的决定。"),
     ("portable","/ˈpɔːtəbl/","adj. 便携的","port 运 + -able 能…的 → 能带走的","a portable computer","便携电脑")]},
   {"rt":"词根 ③ -dict / -dic","mean":"说（say / speak）",
    "hook":"dict → 联想「dictionary 字典（说/词义的集子）」，核心是“说”。",
    "words":[
     ("dictate","/dɪkˈteɪt/","v. 口述，命令","dict 说 + -ate 动 → 说出来 → 口述","The boss dictated a letter.","老板口述了一封信。"),
     ("predict","/prɪˈdɪkt/","v. 预测","pre- 前 + dict 说 → 预先说 → 预言","Scientists predict the weather.","科学家预测天气。"),
     ("contradict","/ˌkɒntrəˈdɪkt/","v. 反驳，矛盾","contra- 反 + dict 说 → 反着说 → 反驳","His words contradict the facts.","他的话与事实矛盾。"),
     ("indicate","/ˈɪndɪkeɪt/","v. 表明，指示","in- 朝向 + dict 说 → 指明 → 指示","The map indicates the way.","地图指示了路线。"),
     ("dedicate","/ˈdedɪkeɪt/","v. 致力于","de- 加强 + dict 说 → 宣示 → 献身","He dedicated himself to research.","他投身研究。")]},
   {"rt":"词根 ④ -mit / -miss","mean":"送 / 派（send）",
    "hook":"mit → 联想「missile 导弹（送出去的武器）」「admit 承认（送进来）」，核心是“送”。",
    "words":[
     ("admit","/ədˈmɪt/","v. 承认，准许进入","ad- 朝向 + mit 送 → 送进来 → 接纳/承认","He admitted his mistake.","他承认了错误。"),
     ("commit","/kəˈmɪt/","v. 犯（错），承诺","com- 共同 + mit 送 → 交付 → 承诺/犯","commit a crime 犯罪；commit to 承诺","犯罪；作出承诺"),
     ("permit","/pəˈmɪt/","v. 允许","per- 穿过 + mit 送 → 放行 → 允许","Smoking is not permitted here.","此处禁止吸烟。"),
     ("submit","/səbˈmɪt/","v. 提交，屈服","sub- 下 + mit 送 → 呈上去 → 提交","Please submit your paper.","请提交论文。"),
     ("mission","/ˈmɪʃn/","n. 任务，使命","-ion 名词 ← miss 送 → 被派出去的事","a business mission","商务使命"),
     ("dismiss","/dɪsˈmɪs/","v. 解雇，解散","dis- 离开 + miss 送 → 打发走 → 解散","The case was dismissed.","案件被驳回。")]},
   {"rt":"词根 ⑤ -struct","mean":"建造（build）",
    "hook":"struct → 联想「structure 结构（建造出来的框架）」，核心是“建造”。",
    "words":[
     ("structure","/ˈstrʌktʃə/","n. 结构，建筑物","struct 建 + -ure 名词","the structure of a sentence","句子结构"),
     ("construct","/kənˈstrʌkt/","v. 建造，构建","con- 共同 + struct 建 → 搭建","construct a bridge","建桥"),
     ("instruct","/ɪnˈstrʌkt/","v. 指导，通知","in- 向内 + struct 建 → 建入脑中 → 教导","The teacher instructed us.","老师指导了我们。"),
     ("destroy","/dɪˈstrɔɪ/","v. 摧毁","de- 否定 + stroy[struct] 建 → 拆掉 → 摧毁","The fire destroyed the building.","大火摧毁了大楼。")]},
 ]},

 {"bid":"b02","label":"第02批 (08-07) · 26词（含第07批 -form 合并）","roots":[
   {"rt":"词根 ① -form","mean":"形 / 形状（form / shape）",
    "hook":"form → 联想「form 表格/形状」「transform 变形（改变形状）」，核心是“形”。",
    "words":[
     ("form","/fɔːm/","n. 形式，表格；v. 形成","本词根原形","Fill in the form.","填表格。"),
     ("reform","/rɪˈfɔːm/","v./n. 改革","re- 再 + form 形 → 重塑 → 改革","They reformed the system.","他们改革了制度。"),
     ("transform","/trænsˈfɔːm/","v. 改变，使变形","trans- 跨越 + form 形 → 变形","Technology transformed our life.","科技改变了我们的生活。"),
     ("inform","/ɪnˈfɔːm/","v. 通知，告知","in- 进入 + form 形 → 赋形/使知晓 → 通知","Please inform me of the change.","请通知我变动。"),
     ("perform","/pəˈfɔːm/","v. 执行，表演","per- 完全 + form 形 → 完成成形 → 执行","The band performed well.","乐队表演出色。"),
     ("formal","/ˈfɔːml/","adj. 正式的","form 形 + -al 形容词 → 成形的/规范的","a formal meeting","正式会议"),
     ("formula","/ˈfɔːmjələ/","n. 公式，配方","form 形 + -ula 小 → 固定形式 → 公式","a chemical formula","化学公式"),
     ("uniform","/ˈjuːnɪfɔːm/","adj. 一致的；n. 制服","uni- 一 + form 形 → 同一形状 → 统一/制服","school uniform","校服")]},
   {"rt":"词根 ② -cess / -ceed / -ced","mean":"行走 / 过程 / 去（go）",
    "hook":"cess → 联想「process 过程（向前走的过程）」「success 成功（走到终点）」，核心是“行走/去”。",
    "words":[
     ("success","/səkˈses/","n. 成功","suc- 下 + cess 走 → 走下去 → 到达 → 成功","Hard work brings success.","努力带来成功。"),
     ("process","/ˈprəʊses/","n. 过程，进程","pro- 向前 + cess 走 → 向前走 → 过程","the learning process","学习过程"),
     ("access","/ˈækses/","n./v. 接近，进入","ac- 朝向 + cess 走 → 走向 → 接近","Get access to the data.","获取数据。"),
     ("exceed","/ɪkˈsiːd/","v. 超过","ex- 出 + ceed 走 → 走出 → 超出","The cost exceeded our budget.","成本超出预算。"),
     ("proceed","/prəˈsiːd/","v. 继续进行","pro- 向前 + ceed 走 → 向前走 → 继续","We proceeded with the plan.","我们推进计划。"),
     ("succeed","/səkˈsiːd/","v. 成功，继承","suc- 下 + ceed 走 → 走下去 → 成功","He succeeded in the exam.","他考试成功了。"),
     ("recede","/rɪˈsiːd/","v. 后退，退去","re- 回 + ced 走 → 往回走 → 后退","The flood receded.","洪水退去。"),
     ("precede","/prɪˈsiːd/","v. 在…之前","pre- 前 + cede 走 → 走在前面 → 先于","A precedes B.","A 在 B 之前。")]},
   {"rt":"词根 ③ -cept","mean":"取 / 拿（take）",
    "hook":"cept → 联想「accept 接受（拿进来）」，核心是“取/拿”。",
    "words":[
     ("accept","/əkˈsept/","v. 接受","ac- 朝向 + cept 取 → 拿进来 → 接受","I accept your invitation.","我接受你的邀请。"),
     ("except","/ɪkˈsept/","prep. 除…之外","ex- 出 + cept 取 → 取出 → 除开","Everyone came except him.","除他外都来了。"),
     ("concept","/ˈkɒnsept/","n. 概念","con- 共同 + cept 取 → 抽取出的共识 → 概念","a new concept","新概念"),
     ("receive","/rɪˈsiːv/","v. 收到","re- 回 + ceive[cept] 取 → 取回 → 收到","I received a gift.","我收到一份礼物。"),
     ("deceive","/dɪˈsiːv/","v. 欺骗","de- 向下 + ceive 取 → 骗取 → 欺骗","Don't deceive others.","别欺骗别人。")]},
   {"rt":"词根 ④ -ject","mean":"扔 / 投（throw）",
    "hook":"ject → 联想「project 项目（向前扔出的东西）」「reject 拒绝（扔回去）」，核心是“扔”。",
    "words":[
     ("reject","/rɪˈdʒekt/","v. 拒绝，驳回","re- 回 + ject 扔 → 扔回去 → 拒绝","They rejected my idea.","他们拒绝了我的想法。"),
     ("project","/ˈprɒdʒekt/","n. 项目；v. 投射","pro- 向前 + ject 扔 → 向前扔 → 投射/项目","a new project","新项目"),
     ("object","/ˈɒbdʒɪkt/","n. 物体；v. 反对","ob- 逆 + ject 扔 → 反着扔 → 反对","I object to this plan.","我反对这个计划。"),
     ("subject","/ˈsʌbdʒɪkt/","n. 主题，科目","sub- 下 + ject 扔 → 被置于下方 → 主题/臣民","the subject of the talk","谈话主题"),
     ("inject","/ɪnˈdʒekt/","v. 注射，注入","in- 向内 + ject 扔 → 扔进去 → 注入","The nurse injected the drug.","护士注射了药物。")]},
 ]},

 {"bid":"b03","label":"第03批 (08-11) · 25词（含第05批 -scrib/-fer 与第07批 -vert 合并）","roots":[
   {"rt":"词根 ① -scrib / -scribe","mean":"写（write）",
    "hook":"scrib → 联想「describe 描述（写下来）」「manuscript 手稿（手写的稿）」，核心是“写”。",
    "words":[
     ("describe","/dɪˈskraɪb/","v. 描述","de- 向下 + scrib 写 → 写下来 → 描述","Can you describe the photo?","你能描述这张照片吗？"),
     ("prescribe","/prɪˈskraɪb/","v. 开处方，规定","pre- 前 + scrib 写 → 预先写 → 开处方","The doctor prescribed medicine.","医生开了药。"),
     ("subscribe","/səbˈskraɪb/","v. 订阅，同意","sub- 下 + scrib 写 → 在名下写 → 订阅","subscribe to a magazine","订阅杂志"),
     ("manuscript","/ˈmænjəskrɪpt/","n. 手稿，原稿","manu- 手 + script 写 → 手写稿","an ancient manuscript","古代手稿"),
     ("inscribe","/ɪnˈskraɪb/","v. 题写，刻","in- 向内 + scrib 写 → 写入 → 题刻","His name was inscribed on the stone.","他的名字刻在石头上。"),
     ("transcript","/ˈtrænskrɪpt/","n. 转录本，成绩单","trans- 跨越 + script 写 → 转写 → 转录","a school transcript","成绩单")]},
   {"rt":"词根 ② -tract","mean":"拉 / 抽（pull）",
    "hook":"tract → 联想「tractor 拖拉机（拉东西的机器）」，核心是“拉”。",
    "words":[
     ("attract","/əˈtrækt/","v. 吸引","at- 朝向 + tract 拉 → 拉过来 → 吸引","The show attracted many people.","演出吸引了许多人。"),
     ("contract","/ˈkɒntrækt/","n. 合同；v. 收缩","con- 共同 + tract 拉 → 拉到一起 → 合同/收缩","sign a contract","签合同"),
     ("distract","/dɪˈstrækt/","v. 使分心","dis- 离开 + tract 拉 → 拉开注意力 → 分心","Don't distract me.","别让我分心。"),
     ("extract","/ɪkˈstrækt/","v. 提取，拔出","ex- 出 + tract 拉 → 拉出 → 提取","extract the tooth","拔牙"),
     ("subtract","/səbˈtrækt/","v. 减去","sub- 下 + tract 拉 → 拉下 → 减去","Subtract 3 from 10.","10减3。")]},
   {"rt":"词根 ③ -vert / -vers","mean":"转 / 转向（turn）",
    "hook":"vert → 联想「convert 转变（转过去）」「universe 宇宙（转成一体的）」，核心是“转”。",
    "words":[
     ("convert","/kənˈvɜːt/","v. 转变，转换","con- 共同 + vert 转 → 转过去 → 转变","convert ideas into action","把想法变为行动"),
     ("reverse","/rɪˈvɜːs/","v. 反转，颠倒","re- 回 + vers 转 → 转回去 → 反转","reverse the order","颠倒顺序"),
     ("universe","/ˈjuːnɪvɜːs/","n. 宇宙","uni- 一 + vers 转 → 转成一体 → 宇宙","the whole universe","整个宇宙"),
     ("advertise","/ˈædvətaɪz/","v. 做广告","ad- 朝向 + vert 转 + -ise → 转向人 → 广告","They advertised the product.","他们为产品做广告。"),
     ("diverse","/daɪˈvɜːs/","adj. 多样的","di- 分开 + vers 转 → 转成不同 → 多样","a diverse culture","多元文化"),
     ("divert","/daɪˈvɜːt/","v. 使转向，转移","di- 分开 + vert 转 → 转开 → 使转向","divert traffic","疏导交通"),
     ("version","/ˈvɜːʃn/","n. 版本，说法","vers 转 + -ion → 转出来的样式 → 版本","the latest version","最新版本")]},
   {"rt":"词根 ④ -fer","mean":"拿 / 带（carry / bring）",
    "hook":"fer → 联想「offer 提供（拿出去）」「transfer 转移（搬运）」，核心是“拿/带”。",
    "words":[
     ("refer","/rɪˈfɜː/","v. 提到，参考","re- 回 + fer 拿 → 拿回来说 → 提及","refer to a dictionary","查词典"),
     ("prefer","/prɪˈfɜː/","v. 更喜欢","pre- 前 + fer 拿 → 先拿 → 偏好","I prefer tea to coffee.","茶咖啡我更爱茶。"),
     ("transfer","/trænsˈfɜː/","v. 转移，调动","trans- 跨越 + fer 拿 → 搬运 → 转移","transfer money","转账"),
     ("differ","/ˈdɪfə/","v. 不同，有分歧","dif- 分开 + fer 拿 → 各拿各的 → 不同","Opinions differ.","意见不一。"),
     ("offer","/ˈɒfə/","v. 提供，提议","of- 朝向 + fer 拿 → 拿出去 → 提供","He offered me a job.","他给了我一份工作。"),
     ("infer","/ɪnˈfɜː/","v. 推断","in- 向内 + fer 拿 → 拿进来判断 → 推断","We inferred the truth.","我们推断出了真相。"),
     ("confer","/kənˈfɜː/","v. 协商，授予","con- 共同 + fer 拿 → 共同拿主意 → 商议","They conferred about the plan.","他们商议了计划。")]},
 ]},

 {"bid":"b04","label":"第04批 (08-13) · 20词","roots":[
   {"rt":"词根 ① -pose / -pos","mean":"放 / 置（put）",
    "hook":"pose → 联想「pose 摆姿势（把身体放好）」「position 位置」，核心是“放”。",
    "words":[
     ("compose","/kəmˈpəʊz/","v. 组成，创作","com- 共同 + pose 放 → 放到一起 → 组成","compose a song","创作歌曲"),
     ("expose","/ɪkˈspəʊz/","v. 暴露，揭露","ex- 出 + pose 放 → 放出来 → 暴露","The truth was exposed.","真相被揭露。"),
     ("oppose","/əˈpəʊz/","v. 反对","op- 逆 + pose 放 → 放在对面 → 反对","We oppose the decision.","我们反对这个决定。"),
     ("propose","/prəˈpəʊz/","v. 提议，求婚","pro- 向前 + pose 放 → 提出 → 提议","He proposed a plan.","他提出了一个计划。"),
     ("impose","/ɪmˈpəʊz/","v. 强加，征税","im- 进 + pose 放 → 放上去 → 强加","impose a tax","征税")]},
   {"rt":"词根 ② -tain / -tend","mean":"握 / 伸（hold / stretch）",
    "hook":"tain → 联想「contain 包含（握在里面）」「maintain 维持（握住所）」，核心是“握/保持”；tend 伸。",
    "words":[
     ("contain","/kənˈteɪn/","v. 包含，容纳","con- 共同 + tain 握 → 握在一起 → 包含","The box contains books.","盒子里装着书。"),
     ("maintain","/meɪnˈteɪn/","v. 维持，保养","main- 手 + tain 握 → 握住所 → 维持","maintain peace","维持和平"),
     ("obtain","/əbˈteɪn/","v. 获得","ob- 朝向 + tain 握 → 握到 → 获得","obtain a degree","获得学位"),
     ("extend","/ɪkˈstend/","v. 延伸，扩展","ex- 出 + tend 伸 → 伸出 → 延伸","extend the deadline","延长期限"),
     ("intend","/ɪnˈtend/","v. 打算，意图","in- 向内 + tend 伸 → 心伸向 → 打算","I intend to go.","我打算去。")]},
   {"rt":"词根 ③ -claim / -clam","mean":"喊 / 叫（shout）",
    "hook":"claim → 联想「claim 声称（大声说）」，核心是“喊/叫”。",
    "words":[
     ("claim","/kleɪm/","v. 声称，要求","本词根原形 → 喊出主张","He claimed the prize.","他认领了奖品。"),
     ("proclaim","/prəˈkleɪm/","v. 宣布","pro- 向前 + claim 喊 → 向前喊 → 宣布","They proclaimed the result.","他们宣布了结果。"),
     ("exclaim","/ɪkˈskleɪm/","v. 惊呼，呼喊","ex- 出 + claim 喊 → 喊出来 → 惊呼","She exclaimed in surprise.","她惊讶地喊道。"),
     ("acclaim","/əˈkleɪm/","v. 称赞，欢呼","ac- 朝向 + claim 喊 → 向…欢呼 → 称赞","The film won acclaim.","影片赢得赞誉。"),
     ("reclaim","/rɪˈkleɪm/","v. 回收，开垦","re- 回 + claim 喊 → 喊回 → 收回","reclaim land","开垦土地")]},
   {"rt":"词根 ④ -duc / -duct","mean":"引 / 导（lead）",
    "hook":"duc → 联想「conduct 引导（带路）」「introduce 介绍（引进）」，核心是“引/领”。",
    "words":[
     ("conduct","/kənˈdʌkt/","v. 进行，引导","con- 共同 + duct 引 → 带 → 引导","conduct an experiment","做实验"),
     ("introduce","/ˌɪntrəˈdjuːs/","v. 介绍，引入","intro- 向内 + duc 引 → 引进 → 介绍","Let me introduce myself.","我来自我介绍。"),
     ("produce","/prəˈdjuːs/","v. 生产，产生","pro- 向前 + duc 引 → 引出 → 生产","The factory produces cars.","工厂生产汽车。"),
     ("reduce","/rɪˈdjuːs/","v. 减少，降低","re- 回 + duc 引 → 引回 → 缩减","reduce the cost","降低成本"),
     ("educate","/ˈedʒukeɪt/","v. 教育","e- 向外 + duc 引 + -ate → 引出潜能 → 教育","educate the children","教育孩子")]},
 ]},

 {"bid":"b05","label":"第05批 (08-14) · 5词（其余 -scrib/-fer/-ject 已并入首现批次，当复习）","roots":[
   {"rt":"词根 ① -sign","mean":"标记 / 信号（mark / sign）",
    "hook":"sign → 联想「sign 标志/签名（做标记）」，核心是“标记”。",
    "words":[
     ("signal","/ˈsɪɡnl/","n. 信号","sign 标记 + -al → 标记物 → 信号","a warning signal","警示信号"),
     ("signify","/ˈsɪɡnɪfaɪ/","v. 表示，意味","sign 标记 + -ify 使 → 使成标记 → 表示","It signifies danger.","这表示危险。"),
     ("design","/dɪˈzaɪn/","v./n. 设计","de- 向下 + sign 标记 → 标出 → 设计","design a logo","设计标志"),
     ("assign","/əˈsaɪn/","v. 分配，指派","as- 朝向 + sign 标记 → 标给 → 分配","assign a task","分配任务"),
     ("resign","/rɪˈzaɪn/","v. 辞职","re- 回 + sign 标记 → 交回署名 → 辞职","He resigned from his job.","他辞了职。")]},
 ]},

 {"bid":"b06","label":"第06批 (08-16) · 18词（含第08批 -gress 合并）","roots":[
   {"rt":"词根 ① -cur / -cours","mean":"跑 / 流（run / flow）",
    "hook":"cur → 联想「current 当前的/水流（跑着的）」，核心是“跑/流”。",
    "words":[
     ("occur","/əˈkɜː/","v. 发生，出现","oc- 朝向 + cur 跑 → 跑来 → 发生","The accident occurred yesterday.","事故昨天发生。"),
     ("recur","/rɪˈkɜː/","v. 重现，反复","re- 回 + cur 跑 → 跑回来 → 反复","The pain recurred.","疼痛又犯了。"),
     ("current","/ˈkʌrənt/","adj. 当前的；n. 水流/电流","cur 跑 + -ent → 跑着的 → 当前的","current affairs","时事"),
     ("currency","/ˈkʌrənsi/","n. 货币，流通","cur 跑 + -ency → 跑动的 → 货币","foreign currency","外币"),
     ("concur","/kənˈkɜː/","v. 同意，同时发生","con- 共同 + cur 跑 → 同跑 → 一致","I concur with you.","我同意你。")]},
   {"rt":"词根 ② -grad / -gress","mean":"步 / 级 / 走（step / go）",
    "hook":"grad → 联想「grade 年级/等级（台阶）」「progress 进步（向前走）」，核心是“步/级”。",
    "words":[
     ("progress","/ˈprəʊɡres/","n./v. 进步，进展","pro- 向前 + gress 走 → 向前走 → 进步","make progress","取得进步"),
     ("gradual","/ˈɡrædʒuəl/","adj. 逐渐的","grad 级 + -ual → 一级级的 → 逐渐的","a gradual change","渐变"),
     ("grade","/ɡreɪd/","n. 年级，等级；v. 评分","grad 级 → 等级","a high grade","高分"),
     ("aggressive","/əˈɡresɪv/","adj. 侵略性的，进取的","ag- 朝向 + gress 走 + -ive → 向前冲的 → 进攻的","an aggressive attitude","咄咄逼人的态度"),
     ("degrade","/dɪˈɡreɪd/","v. 降级，退化","de- 向下 + grad 级 → 降級","degrade the environment","破坏环境"),
     ("congress","/ˈkɒŋɡres/","n. 国会，大会","con- 共同 + gress 走 → 走到一起 → 大会","a medical congress","医学大会"),
     ("digress","/daɪˈɡres/","v. 离题","di- 分开 + gress 走 → 走偏 → 离题","Sorry, I digressed.","抱歉，我跑题了。"),
     ("regress","/rɪˈɡres/","v. 倒退，退化","re- 回 + gress 走 → 往回走 → 倒退","regress to old habits","退回旧习惯")]},
   {"rt":"词根 ③ -loc","mean":"放 / 位置（place）",
    "hook":"loc → 联想「local 当地的（固定在位置的）」，核心是“放/位置”。",
    "words":[
     ("locate","/ləʊˈkeɪt/","v. 定位，位于","loc 放 + -ate → 放在某处 → 定位","locate the city on the map","在地图上找到城市"),
     ("local","/ˈləʊkl/","adj. 当地的，局部的","loc 位置 + -al → 位置的 → 当地的","local food","本地食物"),
     ("location","/ləʊˈkeɪʃn/","n. 位置，地点","loc 放 + -ion → 所放之处","a good location","好位置"),
     ("allocate","/ˈæləkeɪt/","v. 分配","al- 朝向 + loc 放 + -ate → 放给 → 分配","allocate funds","拨款"),
     ("dislocate","/ˈdɪsləkeɪt/","v. 使脱位，扰乱","dis- 离开 + loc 位置 + -ate → 移出位置 → 脱位","dislocate a shoulder","肩脱位")]},
 ]},

 {"bid":"b07","label":"第07批 (08-17) · 9词（-vert/-form 已并入首现批次）","roots":[
   {"rt":"词根 ① -clud / -clus","mean":"关 / 闭（close / shut）",
    "hook":"clud → 联想「include 包含（关在里面）」「exclude 排除（关在外面）」，核心是“关”。",
    "words":[
     ("include","/ɪnˈkluːd/","v. 包含","in- 向内 + clud 关 → 关进里面 → 包含","The price includes tax.","价格含税。"),
     ("exclude","/ɪkˈskluːd/","v. 排除，排斥","ex- 出 + clud 关 → 关在外面 → 排除","exclude the possibility","排除可能"),
     ("conclude","/kənˈkluːd/","v. 总结，结束","con- 共同 + clud 关 → 收拢 → 总结","conclude the meeting","结束会议"),
     ("exclusive","/ɪkˈskluːsɪv/","adj. 独有的，排外的","ex- 外 + clus 关 + -ive → 关在外面的 → 独享的","an exclusive club","私人会所")]},
   {"rt":"词根 ② -pend / -pens","mean":"悬挂 / 花费 / 称重（hang / pay / weigh）",
    "hook":"pend → 联想「depend 依赖（挂在…上）」「expense 花费（称重量支出）」，核心是“悬挂/花费”。",
    "words":[
     ("depend","/dɪˈpend/","v. 依赖，取决于","de- 下 + pend 悬挂 → 挂在…下 → 依靠","It depends on you.","这取决于你。"),
     ("suspend","/səˈspend/","v. 悬挂，暂停","sus- 下 + pend 悬挂 → 吊起 → 悬挂/暂停","suspend the rule","暂停规则"),
     ("expense","/ɪkˈspens/","n. 花费，开销","ex- 出 + pens 称重/付 → 付出 → 花费","at someone's expense","由某人付费"),
     ("expensive","/ɪkˈspensɪv/","adj. 昂贵的","ex- 出 + pens 付 + -ive → 花钱的 → 贵的","an expensive car","昂贵的车"),
     ("pension","/ˈpenʃn/","n. 养老金","pens 付 + -ion → 付出的退休金","receive a pension","领养老金")]},
 ]},

 {"bid":"b08","label":"第08批 (08-18) · 15词（-gress 已并入第06批）","roots":[
   {"rt":"词根 ① -vid / -vis","mean":"看 / 看见（see）",
    "hook":"vis → 联想「visit 参观（去看）」「visual 视觉的」，核心是“看”。",
    "words":[
     ("video","/ˈvɪdiəʊ/","n. 视频","vid 看 + -eo → 能看的 → 视频","watch a video","看视频"),
     ("visible","/ˈvɪzəbl/","adj. 可见的","vis 看 + -ible 能…的 → 能看见的","The star is visible.","星星可见。"),
     ("visit","/ˈvɪzɪt/","v. 参观，拜访","vis 看 + -it → 去看 → 拜访","visit a museum","参观博物馆"),
     ("advise","/ədˈvaɪz/","v. 建议，劝告","ad- 朝向 + vis 看 → 看法给人 → 劝告","I advise you to rest.","我劝你休息。"),
     ("evident","/ˈevɪdənt/","adj. 明显的","e- 向外 + vid 看 + -ent → 看得出来的 → 明显的","an evident mistake","明显的错误")]},
   {"rt":"词根 ② -press","mean":"压 / 按（press）",
    "hook":"press → 联想「press 按压」「pressure 压力」，核心是“压”。",
    "words":[
     ("press","/pres/","v. 压，按；n. 新闻界","本词根原形 → 压","press the button","按按钮"),
     ("pressure","/ˈpreʃə/","n. 压力","press 压 + -ure → 压的状态 → 压力","under pressure","在压力下"),
     ("compress","/kəmˈpres/","v. 压缩","com- 共同 + press 压 → 压在一起 → 压缩","compress the file","压缩文件"),
     ("depress","/dɪˈpres/","v. 使沮丧，压下","de- 向下 + press 压 → 压低 → 使消沉","The news depressed him.","消息让他沮丧。"),
     ("express","/ɪkˈspres/","v. 表达；adj. 特快的","ex- 出 + press 压 → 压出 → 表达","express your feelings","表达感受")]},
   {"rt":"词根 ③ -rupt","mean":"断 / 破（break）",
    "hook":"rupt → 联想「interrupt 打断（破开）」「bankrupt 破产（钱袋破了）」，核心是“断/破”。",
    "words":[
     ("rupture","/ˈrʌptʃə/","n./v. 破裂","rupt 破 + -ure → 破","a rupture in relations","关系破裂"),
     ("abrupt","/əˈbrʌpt/","adj. 突然的，陡峭的","ab- 离开 + rupt 破 → 断开的 → 突兀的","an abrupt stop","急停"),
     ("bankrupt","/ˈbæŋkrʌpt/","adj. 破产的","bank 钱袋 + rupt 破 → 钱袋破了 → 破产","go bankrupt","破产"),
     ("corrupt","/kəˈrʌpt/","adj. 腐败的；v. 使堕落","cor- 全部 + rupt 破 → 全坏 → 腐败","a corrupt official","贪官"),
     ("disrupt","/dɪsˈrʌpt/","v. 扰乱，中断","dis- 分开 + rupt 破 → 破开 → 打乱","disrupt the meeting","扰乱会议")]},
 ]},

 {"bid":"b09","label":"第09批 (08-19) · 20词","roots":[
   {"rt":"词根 ① -voc / -vok","mean":"叫 / 声 / 呼（voice / call）",
    "hook":"voc → 联想「voice 声音」「vocal 嗓音的」，核心是“叫/声”。",
    "words":[
     ("voice","/vɔɪs/","n. 声音，嗓音","voc 声 + -e → 声音","in a loud voice","大声地"),
     ("vocal","/ˈvəʊkl/","adj. 嗓音的，直言的","voc 声 + -al → 声音的","vocal music","声乐"),
     ("advocate","/ˈædvəkeɪt/","v. 提倡；n. 倡导者","ad- 朝向 + voc 叫 + -ate → 叫好 → 提倡","advocate peace","提倡和平"),
     ("evoke","/ɪˈvəʊk/","v. 唤起，引起","e- 向外 + vok 叫 → 叫出 → 唤起","evoke memories","唤起回忆"),
     ("provoke","/prəˈvəʊk/","v. 挑衅，激起","pro- 向前 + vok 叫 → 向前叫嚣 → 激怒","provoke anger","激起愤怒")]},
   {"rt":"词根 ② -sens / -sent","mean":"感觉 / 感知（feel / sense）",
    "hook":"sens → 联想「sense 感觉」「sensitive 敏感的」，核心是“感觉”。",
    "words":[
     ("sense","/sens/","n. 感觉，意义","本词根原形 → 感觉","common sense","常识"),
     ("sensible","/ˈsensəbl/","adj. 明智的，合理的","sens 感觉 + -ible → 有感应的 → 明智的","a sensible decision","明智的决定"),
     ("sensitive","/ˈsensətɪv/","adj. 敏感的","sens 感觉 + -itive → 感觉强的 → 敏感的","sensitive skin","敏感肌肤"),
     ("consent","/kənˈsent/","n./v. 同意","con- 共同 + sent 感觉 → 同感 → 同意","give consent","同意"),
     ("resent","/rɪˈzent/","v. 怨恨","re- 回 + sent 感觉 → 反感 → 怨恨","He resented the comment.","他怨恨那句评论。")]},
   {"rt":"词根 ③ -nov","mean":"新 / 更新（new）",
    "hook":"nov → 联想「novel 新颖的」「innovate 创新（引入新）」，核心是“新”。",
    "words":[
     ("novel","/ˈnɒvl/","adj. 新颖的；n. 小说","nov 新 + -el → 新的 → 小说","a novel idea","新点子"),
     ("innovate","/ˈɪnəveɪt/","v. 创新","in- 进入 + nov 新 + -ate → 引入新 → 创新","innovate the process","革新流程"),
     ("innovation","/ˌɪnəˈveɪʃn/","n. 创新，革新","nov 新 + -ation → 新事物","technical innovation","技术创新"),
     ("novice","/ˈnɒvɪs/","n. 新手","nov 新 + -ice → 新人 → 新手","a novice driver","新司机"),
     ("renew","/rɪˈnjuː/","v. 更新，续期","re- 再 + new[nov] 新 → 再新 → 更新","renew the license","续证")]},
   {"rt":"词根 ④ -spir","mean":"呼吸 / 精神（breath / spirit）",
    "hook":"spir → 联想「spirit 精神（一口气/生命力）」「inspire 鼓舞（吹入气息）」，核心是“呼吸/精神”。",
    "words":[
     ("spirit","/ˈspɪrɪt/","n. 精神，灵魂","spir 呼吸 + -it → 生命气息 → 精神","in high spirits","情绪高涨"),
     ("inspire","/ɪnˈspaɪə/","v. 鼓舞，启发","in- 向内 + spir 呼吸 → 吹入气息 → 鼓舞","The teacher inspired us.","老师鼓舞了我们。"),
     ("aspire","/əˈspaɪə/","v. 渴望，追求","a- 朝向 + spir 呼吸 → 向往 → 渴望","aspire to be a doctor","渴望成为医生"),
     ("expire","/ɪkˈspaɪə/","v. 到期，呼气","ex- 出 + spir 呼吸 → 呼出 → 到期","The contract expired.","合同到期了。"),
     ("conspire","/kənˈspaɪə/","v. 密谋，共谋","con- 共同 + spir 呼吸 → 同呼吸 → 勾结","They conspired against him.","他们密谋反对他。")]},
 ]},

 {"bid":"b10","label":"第10批 (08-20) · 20词（对照本总表去重，零重复）","roots":[
   {"rt":"词根 ① -cap / -cip","mean":"抓 / 取（take / seize）",
    "hook":"cap → 联想「capture 捕获（抓住）」「capital 首都（抓权之地）」，核心是“抓/取”。",
    "words":[
     ("capture","/ˈkæptʃə/","v. 捕获，占领","cap 抓 + -ture → 抓住","capture the moment","捕捉瞬间"),
     ("capable","/ˈkeɪpəbl/","adj. 有能力的","cap 抓 + -able 能…的 → 能抓事 → 有能力的","a capable leader","能干的领导"),
     ("capacity","/kəˈpæsəti/","n. 容量，能力","cap 抓 + -acity → 抓的量 → 容量","a large capacity","大容量"),
     ("captive","/ˈkæptɪv/","adj. 被俘的；n. 俘虏","cap 抓 + -ive → 被抓的","hold someone captive","囚禁某人"),
     ("occupy","/ˈɒkjupaɪ/","v. 占据，占用","oc- 朝向 + cup[y] 抓 → 抓住 → 占据","occupy the seat","占座")]},
   {"rt":"词根 ② -leg / -lig","mean":"选 / 绑 / 读（choose / bind / read）",
    "hook":"leg → 联想「legal 合法的（绑定的规则）」「college 学院（选出来的一群）」，核心是“选/绑”。",
    "words":[
     ("legal","/ˈliːɡl/","adj. 合法的","leg 法/绑 + -al → 合法的","legal rights","合法权利"),
     ("legend","/ˈledʒənd/","n. 传说，图例","leg 读 + -end → 被读诵的 → 传说","a famous legend","著名传说"),
     ("college","/ˈkɒlɪdʒ/","n. 学院，大学","col- 共同 + leg 选 → 选在一起 → 学院","go to college","上大学"),
     ("eligible","/ˈelɪdʒəbl/","adj. 有资格的","e- 向外 + lig 选 + -ible → 被选出的 → 合格的","eligible for the job","有资格任职"),
     ("privilege","/ˈprɪvəlɪdʒ/","n. 特权","priv- 私 + leg 法 → 私法 → 特权","a special privilege","特殊特权")]},
   {"rt":"词根 ③ -mand / -mend","mean":"命令 / 托付（order / entrust）",
    "hook":"mand → 联想「command 命令（交托指令）」，核心是“命令/托付”。",
    "words":[
     ("command","/kəˈmɑːnd/","v./n. 命令，指挥","com- 共同 + mand 托付 → 委命 → 指挥","command the army","指挥军队"),
     ("demand","/dɪˈmɑːnd/","v./n. 要求，需求","de- 向下 + mand 命令 → 下命令 → 要求","meet the demand","满足需求"),
     ("recommend","/ˌrekəˈmend/","v. 推荐，建议","re- 再 + com- + mend 托付 → 托付 → 推荐","I recommend this book.","我推荐这本书。"),
     ("mandatory","/ˈmændətəri/","adj. 强制的，义务的","mand 命令 + -atory → 命令的 → 必须的","mandatory training","强制培训"),
     ("commander","/kəˈmɑːndə/","n. 指挥官","command 指挥 + -er 人 → 指挥官","a troop commander","部队指挥官")]},
   {"rt":"词根 ④ -min / -minu","mean":"小（small / less）",
    "hook":"min → 联想「minor 较小的」「minimum 最小的」，核心是“小”。",
    "words":[
     ("minute","/ˈmɪnɪt/","n. 分钟；/maɪˈnjuːt/ adj. 微小的","min 小 → 微小","a minute error","微小的错误"),
     ("minimum","/ˈmɪnɪməm/","n./adj. 最小（值）","min 小 + -imum → 最小","the minimum wage","最低工资"),
     ("minor","/ˈmaɪnə/","adj. 较小的，次要的","min 小 + -or → 较小的","a minor problem","小问题"),
     ("minority","/maɪˈnɒrəti/","n. 少数，少数民族","min 小 + -or + -ity → 少数","a minority group","少数群体"),
     ("diminish","/dɪˈmɪnɪʃ/","v. 减少，削弱","di- 分开 + min 小 + -ish → 变小 → 减少","diminish the risk","降低风险")]},
 ]},
]

# 追加未来 10 批（第 11–20 批，预生成、待排期），与第 01–10 批合并为完整 20 批
B = B + FUTURE

CSS = """<style>
* { box-sizing: border-box; }
body { font-family: system-ui, "Segoe UI", "Microsoft YaHei", sans-serif;
       background:#f6f7f9; color:#1f2937; max-width:940px; margin:0 auto; padding:22px 18px 60px; line-height:1.6; }
h1 { font-size:24px; margin:0 0 4px; }
.sub { color:#6b7280; font-size:14px; margin:0 0 18px; }
.note { background:#fffbeb; border:1px solid #fde68a; border-radius:8px; padding:10px 14px; font-size:13px; color:#92400e; margin:0 0 22px; }
.batch { margin:26px 0; }
.batch > h2 { color:#fff; padding:9px 16px; border-radius:8px; font-size:17px; margin:0 0 14px; }
.root { border:1px solid #e5e7eb; border-left:6px solid #999; border-radius:8px; padding:12px 16px; margin:14px 0; background:#fff; }
.rt { font-weight:700; font-size:15.5px; margin-bottom:2px; }
.mean { font-weight:400; color:#374151; }
.hook { background:#fff7ed; border-left:3px solid #f59e0b; padding:6px 11px; margin:8px 0; border-radius:4px; font-size:13.5px; color:#9a3412; }
.w { padding:7px 0; border-bottom:1px dashed #eef0f2; font-size:14px; }
.w:last-child { border-bottom:none; }
.w b { color:#111827; font-size:14.5px; }
.ipa { color:#6b7280; font-style:italic; margin:0 4px; }
.brk { color:#b45309; }
.ex { display:block; color:#374151; margin-top:3px; font-size:13px; }
audio { width:100%; margin-top:6px; }
.batchPlay { margin-left:10px; border:none; border-radius:6px; padding:3px 12px; font-size:12px;
  font-weight:600; color:#fff; background:rgba(255,255,255,.28); cursor:pointer; vertical-align:middle; }
.batchPlay:hover { background:rgba(255,255,255,.45); }
.batchPlay.on { background:#fff; color:#111; }
.back-home{position:fixed;right:18px;bottom:18px;z-index:9999;display:inline-flex;align-items:center;gap:6px;padding:10px 16px;background:#2C2C2A;color:#fff;font-size:14px;font-weight:600;text-decoration:none;border-radius:999px;box-shadow:0 4px 14px rgba(0,0,0,.22);font-family:-apple-system,"PingFang SC","Microsoft YaHei",sans-serif}
.back-home:active{transform:scale(.96)}
@media(max-width:600px){.back-home{padding:9px 13px;font-size:13px;right:12px;bottom:12px}}
footer { margin-top:34px; font-size:12.5px; color:#9ca3af; border-top:1px solid #e5e7eb; padding-top:14px; }
</style>"""

def esc(s):
    return s.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")

html = ["<!DOCTYPE html>", "<html lang='zh-CN'>", "<head>",
        "<meta charset='utf-8'>",
        "<meta name='viewport' content='width=device-width, initial-scale=1'>",
        "<title>考研英语 · 词根单词总表（组网格式）</title>", CSS, "</head>", "<body>"]
html.append("<a href='index.html' class='back-home' title='返回备考中心首页'>← 目录</a>")
html.append("<h1>考研英语 · 词根单词总表（词根组网法）</h1>")
html.append("<p class='sub'>按「第一批词根组网」格式整理 · 每个词根配记忆钩子，每个单词结构拆解+例句 · 相邻批次配色不同 · 跨批重复词根已合并</p>")
html.append("<div class='note'>说明：第 01–10 批（34 词根族 / 185 词，跨批重复已合并）+ 第 11–20 批（40 词根族 / 200 词，预生成·待排期），合计 <b>20 批 / 74 词根族 / 385 个不重复词</b>。"
            "第 01–10 批重复族（-scrib/-fer/-ject 在第05批；-cess 在第06批；-vert/-form 在第07批；-gress 在第08批）均已并入首现批次。"
            "下方按批次展示，每批一种颜色，相邻批次颜色不同。</div>")

for batch in B:
    c = COLORS[batch["bid"]]
    bid = batch["bid"]
    html.append(f"<div class='batch' id='batch-{bid}' data-batch='{bid}'>"
                f"<h2 style='background:{c}'>{esc(batch['label'])} "
                f"<button class='batchPlay' data-batch='{bid}' title='只连续播放本批次内所有单词，不跨批'>▶ 联播本批</button></h2>")
    for r in batch["roots"]:
        html.append(f"<div class='root' style='border-left-color:{c}'>")
        html.append(f"<div class='rt' style='color:{c}'>{esc(r['rt'])} <span class='mean'>= {esc(r['mean'])}</span></div>")
        html.append(f"<p class='hook'>钩子：{esc(r['hook'])}</p>")
        for (w, ipa, pm, brk, en, zh) in r["words"]:
            html.append(
                f"<div class='w'><b>{esc(w)}</b><span class='ipa'>{esc(ipa)}</span>{esc(pm)}"
                f"<span class='brk'>（{esc(brk)}）</span>"
                f"<span class='ex'>例：{esc(en)} {esc(zh)}</span>"
                f"<audio controls preload='none' src='audio/{esc(w)}.mp3'></audio></div>")
        html.append("</div>")
    html.append("</div>")

html.append("<footer>数据来源：第 01–10 批来自 01~10_词根词表.txt（一手源文件）· 第 11–20 批来自 future_batches.py（预生成·待排期）· 累计 20 批 · 本表为去重合并后的单一事实源。每词内嵌听书音频，每批可「▶ 联播本批」（仅本批内连续播放）。</footer>")
html.append("""<script>
const audios = Array.from(document.querySelectorAll('.batch audio'));
let activeBatch = null;

// 同一时间只允许一个音频播放 + 每次都从头开始
audios.forEach(a => a.addEventListener('play', () => {
  audios.forEach(o => { if (o !== a) o.pause(); });
  if (a.currentTime > 0.3) a.currentTime = 0;
}));

// 联播：播完自动续播本批下一个，本批播完即停（不跨批）
audios.forEach(a => a.addEventListener('ended', () => {
  if (!activeBatch) return;
  const sec = a.closest('.batch');
  if (!sec || sec.dataset.batch !== activeBatch) return;
  const list = Array.from(sec.querySelectorAll('audio'));
  const idx = list.indexOf(a);
  if (idx >= 0 && idx < list.length - 1) {
    const n = list[idx + 1];
    n.currentTime = 0;
    n.play();
  } else {
    activeBatch = null;
    updateBtns();
  }
}));

function updateBtns(){
  document.querySelectorAll('.batchPlay').forEach(b => b.classList.toggle('on', b.dataset.batch === activeBatch));
}
function playBatch(bid){
  if (activeBatch === bid) { activeBatch = null; audios.forEach(o => o.pause()); updateBtns(); return; }
  activeBatch = bid;
  audios.forEach(o => o.pause());
  const sec = document.getElementById('batch-' + bid);
  const first = sec && sec.querySelector('audio');
  if (first) { first.currentTime = 0; first.play(); }
  updateBtns();
}
document.querySelectorAll('.batchPlay').forEach(b => b.addEventListener('click', () => playBatch(b.dataset.batch)));
</script>""")
html.append("</body></html>")

out_html = "\n".join(html)
with io.open("单词总表.html", "w", encoding="utf-8") as f:
    f.write(out_html)

# ---- 同步生成纯文本去重锚点版 单词总表.txt ----
lines = []
lines.append("="*64)
lines.append("考研英语 · 词根单词总表（去重合并锚点版 · 组网格式整理后）")
lines.append("最近更新：2026-08-20 · Day15 · 累计 20 批（第11-20批为预生成·待排期）")
lines.append("数据来源：第01-10批来自 01~10_词根词表.txt；第11-20批来自 future_batches.py（非记忆）")
lines.append("去重结果：第01-10批 208 词条合并为 34 族/185 词；第11-20批 40 族/200 词；合计 74 族/385 不重复词")
lines.append("用途：每次生成新词根前先扫「一、已用词根族清单」，避免跨批复用旧族")
lines.append("="*64)
lines.append("")
lines.append("【一、已用词根族清单（生成新批前先扫这一栏 · 已合并去重）】")
fam_lines = []
for i, batch in enumerate(B, 1):
    roots = "  ".join(r["rt"].split(" ", 2)[-1] for r in batch["roots"])
    fam_lines.append(f"第{i:02d}批: {roots}")
lines.append("\n".join(fam_lines))
lines.append("")
lines.append("【二、按批次全词表（合并后）】")
for i, batch in enumerate(B, 1):
    total = sum(len(r["words"]) for r in batch["roots"])
    lines.append("")
    lines.append(f"=== 第{i:02d}批 {batch['label'].split('·')[0].strip()} {total}词 ===")
    for r in batch["roots"]:
        words = ", ".join(w for (w, *_ ) in r["words"])
        lines.append(f"{r['rt'].split(' ',2)[-1]} {r['mean'].split('（')[0]}: {words}")
lines.append("")
lines.append("【三、重复族合并记录（审计确认）】")
lines.append("- 第05批 -scrib 并入第03批；新增 transcript")
lines.append("- 第05批 -fer 并入第03批；新增 infer / confer")
lines.append("- 第05批 -ject 并入第02批（全为重复，无新增）")
lines.append("- 第06批 -cess/-ced 并入第02批；新增 succeed / recede / precede")
lines.append("- 第07批 -vert/-vers 并入第03批；新增 divert / version")
lines.append("- 第07批 -form 并入第02批；新增 form / uniform")
lines.append("- 第08批 -gress 并入第06批；新增 congress / digress / regress")
lines.append("="*64)

out_txt = "\n".join(lines)
with io.open("单词总表.txt", "w", encoding="utf-8") as f:
    f.write(out_txt)

# ---- 同步导出 TTS 数据集 words_tts.json（单一事实源，供 gen_audio.py 使用）----
import json
tts_words = []
for bi, batch in enumerate(B, 1):
    for r in batch["roots"]:
        for (w, ipa, pm, brk, en, zh) in r["words"]:
            tts_words.append({
                "word": w, "ipa": ipa, "meaning": pm,
                "example_en": en, "example_zh": zh,
                "batch": bi, "root": r["rt"].split(" ", 2)[-1],
            })
with io.open("words_tts.json", "w", encoding="utf-8") as f:
    json.dump(tts_words, f, ensure_ascii=False, indent=1)
print("OK: words_tts.json words=", len(tts_words))

print("OK: 单词总表.html bytes=", len(out_html.encode("utf-8")))
print("OK: 单词总表.txt bytes=", len(out_txt.encode("utf-8")))
print("批次数:", len(B), " 词根族数:", sum(len(b['roots']) for b in B),
      " 单词总数:", sum(len(r['words']) for b in B for r in b['roots']))
