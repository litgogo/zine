/* =========================================================================
 *  检索墙数据 —— 全站唯一数据源（Single Source of Truth）
 *
 *  以前 index.html 和 archive.html 各存一份 WALL，历史上每期只更一份，
 *  导致 archive 长期漏更 5 期。2026-09-11 抽出为独立数据文件，两页共用。
 *
 *  新增一期收听：只在下面 WALL 数组顶部加一行即可，两页同时生效。
 *  字段：date(YYYY.MM.DD) / show(一档节目,只存基名) / title(单集)
 *        ep(期号,可空) / duration(时:分:秒,可空) / guest(嘉宾短名,可空)
 *        link(落地页,可空) / status: zine 已转 zine · pending 待筛选
 *                              transcript 逐字稿 · saved 仅收藏
 *        star: true = 特藏 · style: 'cornell' = 康奈尔笔记风格标签
 *  书目封面：BOOK_COVER 按节目名给封面路径（有图加，无图自动用素净书封占位）
 * ========================================================================= */

var STYLE_LABEL = { cornell: '康奈尔笔记' };

var WALL = [
{"date":"2026.09.14","show":"西西弗高速","title":"一个人要消化多少信息，才能成为一个社会人？","ep":"#30","duration":"1:51:00","status":"zine","style":"cornell","link":"zines/20260914-xixifei-e30.html"},
{"date":"2026.09.11","show":"自习室 STUDY ROOM","guest":"Casey Means","title":"好能量：把细胞作为方法","ep":"105","duration":"1:19:00","status":"zine","style":"cornell","link":"zines/20260911-zixishi-105-hao-nengliang.html"},
{"date":"2026.09.08","show":"岩中花述","guest":"庆山","title":"从前要如我所愿，现在接受如其所是","ep":"S9E8","duration":"1:55:00","status":"zine","link":"zines/20260908-yanzhonghuashu-qingshan.html"},
{"date":"2026.09.07","show":"长谈","guest":"程乐松","title":"让我换个说法：活得哲学一点","ep":"Ep64","duration":"2:55:25","status":"zine","link":"zines/20260907-changtan-chenglesong.html"},
{"date":"2026.09.05","show":"Coffee Plus","guest":"郭晓妍","title":"谁说是「老登的灯」？重新认识虹吸咖啡","ep":"#114","duration":"1:36:00","status":"zine","link":"zines/20260905-coffeeplus-hongxi.html"},
{"date":"2026.09.04","show":"知本论","guest":"程乐松","title":"过度追求人生确定性，是个陷阱","ep":"vol.170","duration":"1:06:00","status":"zine","link":"zines/20260904-zhibenlun-liubai.html"},
{"date":"2026.09.01","show":"无人知晓","guest":"孟岩","title":"我们从未看见彼此","ep":"E46","duration":"1:15:47","status":"zine","link":"zines/20260901-wurenzhixiao-weicengkanjian.html","star":true},
{"date":"2026.08.19","show":"自习室 STUDY ROOM","guest":"花卷 × 自习室","title":"影响力｜用七条法则拿捏人性","duration":"1:25:25","status":"zine","link":"zines/20260819-yingxiangli-qitiao.html"},
{"date":"2026.08.14","show":"新生PLUS","guest":"蔡康永 × 詹青云","title":"蔡康永×詹青云：40岁找到的是原则，而不是答案","status":"zine","link":"zines/20260814-newplus-principle.html"},
{"date":"2026.08.14","show":"出逃在即","guest":"出逃studio","title":"为什么你很难找到 deeptalk 的人","status":"zine","link":"zines/20260814-chutao-deeptalk.html"},
{"date":"2026.08.12","show":"展开讲讲","guest":"洞姐 / 康堤 / 王老师","title":"只要你学得足够慢","ep":"第100期","status":"zine","link":"zines/20260812-zhankai-100.html"},
{"date":"2026.08.06","show":"声东击西","guest":"贾扬清 × 徐涛","title":"从「AI 已死」到「AI 颠覆世界」","ep":"#399(十周年)","status":"zine","link":"zines/20260806-shengdong-jia-yangqing.html"},
{"date":"2026.07.30","show":"新世相","guest":"金靖","title":"活下来，然后为彼此鼓掌","duration":"0:26:14","status":"zine","link":"zines/20260730-xinshixiang-jinjing.html"},
{"date":"2026.07.14","show":"西西弗高速","guest":"女性与叙事","title":"谁在讲述，又为了什么而讲述？","ep":"No.28","status":"zine","link":"zines/20260714-xixifei-nvxing-xushi.html"},
{"date":"2026.07.08","show":"鲁豫慢谈","guest":"姜思达 × 鲁豫","title":"两个高敏感文艺青年","status":"zine","link":"zines/20260708-luyu-jiangsida.html"},
{"date":"2026.07.07","show":"Coffee Plus","guest":"Lema","title":"眼看它起朱楼","ep":"#110","duration":"1:38:59","status":"zine","link":"zines/20260707-seesaw-lema.html"},
{"date":"2026.07.06","show":"半拿铁","guest":"热点观察","title":"热点慢点喝","ep":"No.41","status":"zine","link":"zines/20260706-bannatie.html"},
{"date":"2026.06.11","show":"鲁豫慢谈","guest":"张泉灵 × 鲁豫","title":"AI 时代，人往哪放？","status":"zine","link":"zines/20260611-luyu-zhangquanling.html"},
{"date":"2026.06.09","show":"西西弗高速","guest":"J / 康","title":"致命剂量","ep":"#27","status":"zine","link":"zines/20260609-xixifei-jiliang.html"},
{"date":"2026.06.03","show":"Coffee Plus","guest":"老王","title":"不卖只送的手冲哲学","status":"zine","link":"zines/20260603-coffeeplus-wang.html"},
{"date":"2026.05.02","show":"鲁豫慢谈","guest":"罗翔","title":"在命运的剧本揭晓前尽力扮演好自己的角色","status":"zine","link":"zines/20260502-luyu-luoxiang.html"},
{"date":"2026.04.28","show":"张小珺商业访谈录","guest":"谢赛宁","title":"世界模型与人生梯度","ep":"#133","status":"zine","link":"zines/20260428-xiesaining.html"},
{"date":"2026.04.18","show":"西西弗高速","guest":"李清照 / 丁玲 / 萧红","title":"女性心灵史","ep":"#25","status":"zine","link":"zines/20260418-xixifei-nvxing.html"},
{"date":"2026.04.14","show":"声东击西","guest":"Junyu / Justin","title":"Vibe Coding 与龙虾","ep":"#384","status":"zine","link":"zines/20260414-shengdong-xi-vibe.html"},
{"date":"2026.04.13","show":"知行小酒馆","guest":"施展","title":"宏大叙事与个人命运","ep":"E231","status":"zine","link":"zines/20260413-zhixing-zhanshi.html"},
{"date":"2026.03.20","show":"无人知晓","guest":"李继刚","title":"人何以自处","ep":"E45","duration":"3:26:38","status":"zine","link":"zines/20260320-wurenzhixiao-lijigang.html"},
{"date":"2026.03.18","show":"你，静不下来","guest":"车璐 × 李静 × 养鸡","title":"稳住身体，就是稳住你人生的底盘","duration":"1:00:21","status":"zine","link":"zines/20260318-jingbuxialai-chelu.html"}
];

var BOOK_COVER = {
  "长谈": "covers/logo-changtan-xhs.jpg",
  "无人知晓": "covers/logo-wurenzhixiao-xhs.jpg",
  "自习室 STUDY ROOM": "covers/logo-zixishi-xhs.jpg",
  "声东击西": "covers/logo-shengdong-jixi-xhs.jpg",
  "新世相": "covers/logo-xinshixiang-xhs.jpg",
  "你，静不下来": "covers/logo-nijingbuxialai-xhs.jpg",
  "知行小酒馆": "covers/logo-zhixing-xiaojiuguan-xhs.jpg",
  "半拿铁": "covers/logo-bannatie-xhs.jpg",
  "展开讲讲": "covers/logo-zhankai-jiangjiang-xhs.jpg",
  "西西弗高速": "covers/logo-xixifu-gaosu-xhs.jpg",
  "Coffee Plus": "covers/logo-coffeeplus-xhs.jpg",
  "张小珺商业访谈录": "covers/logo-zhangxiaojun-xhs.jpg",
  "知本论": "covers/logo-zhibenlun-xhs.jpg",
  "岩中花述": "covers/logo-yanzhonghuashu-xhs.png"
};

var STATUS_LABEL = { zine:"已转zine", pending:"待筛选", transcript:"逐字稿", saved:"仅收藏" };
var STATUS_CLASS = { zine:"st-zine", pending:"st-pending", transcript:"st-transcript", saved:"st-saved" };
