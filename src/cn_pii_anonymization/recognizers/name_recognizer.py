"""
中国姓名识别器

识别中文姓名，结合NER和姓氏库进行验证。
支持PaddleNLP LAC模型的NER结果。
"""

from typing import Any, ClassVar

from presidio_analyzer import RecognizerResult
from presidio_analyzer.nlp_engine import NlpArtifacts

from cn_pii_anonymization.recognizers.base import CNPIIRecognizer
from cn_pii_anonymization.utils.logger import get_logger

logger = get_logger(__name__)


class CNNameRecognizer(CNPIIRecognizer):
    """
    中文姓名识别器

    识别中文姓名，支持以下特征：
    - 使用PaddleNLP LAC NER识别PER/PERSON实体
    - 结合中国常见姓氏库验证
    - 支持复姓识别
    - 支持2-4字姓名

    Attributes:
        COMMON_SURNAMES: 常见单姓列表
        COMPOUND_SURNAMES: 复姓列表
        CONTEXT_WORDS: 上下文关键词列表

    Example:
        >>> recognizer = CNNameRecognizer()
        >>> results = recognizer.analyze(
        ...     "联系人：张三",
        ...     ["CN_NAME"],
        ...     nlp_artifacts
        ... )
        >>> print(results[0].entity_type)
        CN_NAME
    """

    COMMON_SURNAMES: ClassVar[set[str]] = {
        "王",
        "李",
        "张",
        "刘",
        "陈",
        "杨",
        "赵",
        "黄",
        "周",
        "吴",
        "徐",
        "孙",
        "胡",
        "朱",
        "高",
        "林",
        "何",
        "郭",
        "马",
        "罗",
        "梁",
        "宋",
        "郑",
        "谢",
        "韩",
        "唐",
        "冯",
        "于",
        "董",
        "萧",
        "程",
        "曹",
        "袁",
        "邓",
        "许",
        "傅",
        "沈",
        "曾",
        "彭",
        "吕",
        "苏",
        "卢",
        "蒋",
        "蔡",
        "贾",
        "丁",
        "魏",
        "薛",
        "叶",
        "阎",
        "余",
        "潘",
        "杜",
        "戴",
        "夏",
        "钟",
        "汪",
        "田",
        "任",
        "姜",
        "范",
        "方",
        "石",
        "姚",
        "谭",
        "廖",
        "邹",
        "熊",
        "金",
        "陆",
        "郝",
        "孔",
        "白",
        "崔",
        "康",
        "毛",
        "邱",
        "秦",
        "江",
        "史",
        "顾",
        "侯",
        "邵",
        "孟",
        "龙",
        "万",
        "段",
        "漕",
        "钱",
        "汤",
        "尹",
        "黎",
        "易",
        "常",
        "武",
        "乔",
        "贺",
        "赖",
        "龚",
        "文",
        "庞",
        "樊",
        "兰",
        "殷",
        "施",
        "陶",
        "洪",
        "翟",
        "安",
        "颜",
        "倪",
        "严",
        "牛",
        "温",
        "芦",
        "季",
        "俞",
        "章",
        "鲁",
        "葛",
        "伍",
        "韦",
        "申",
        "尚",
        "卜",
        "戚",
        "乌",
        "焦",
        "巴",
        "弓",
        "牧",
        "隗",
        "山",
        "谷",
        "车",
        "宓",
        "蓬",
        "全",
        "郗",
        "班",
        "仰",
        "秋",
        "仲",
        "伊",
        "宫",
        "宁",
        "仇",
        "栾",
        "暴",
        "甘",
        "钭",
        "厉",
        "戎",
        "祖",
        "符",
        "景",
        "詹",
        "束",
        "幸",
        "司",
        "韶",
        "郜",
        "蓟",
        "薄",
        "印",
        "宿",
        "怀",
        "蒲",
        "台",
        "丛",
        "鄂",
        "索",
        "咸",
        "籍",
        "卓",
        "蔺",
        "屠",
        "蒙",
        "池",
        "阴",
        "郁",
        "胥",
        "能",
        "苍",
        "双",
        "闻",
        "莘",
        "党",
        "贡",
        "劳",
        "逄",
        "姬",
        "扶",
        "堵",
        "冉",
        "宰",
        "郦",
        "雍",
        "却",
        "璩",
        "桑",
        "桂",
        "濮",
        "寿",
        "通",
        "边",
        "扈",
        "燕",
        "冀",
        "郏",
        "浦",
        "农",
        "别",
        "庄",
        "晏",
        "柴",
        "瞿",
        "充",
        "慕",
        "连",
        "茹",
        "习",
        "宦",
        "艾",
        "鱼",
        "容",
        "向",
        "古",
        "慎",
        "戈",
        "庚",
        "终",
        "暨",
        "居",
        "衡",
        "步",
        "都",
        "耿",
        "满",
        "弘",
        "匡",
        "国",
        "寇",
        "广",
        "禄",
        "阙",
        "东",
        "殴",
        "殳",
        "沃",
        "利",
        "蔚",
        "越",
        "夔",
        "隆",
        "师",
        "巩",
        "厍",
        "聂",
        "晁",
        "勾",
        "敖",
        "融",
        "冷",
        "訾",
        "辛",
        "阚",
        "那",
        "简",
        "饶",
        "空",
        "毋",
        "沙",
        "乜",
        "养",
        "鞠",
        "须",
        "丰",
        "巢",
        "关",
        "蒯",
        "相",
        "查",
        "后",
        "荆",
        "红",
        "游",
        "竺",
        "权",
        "逯",
        "盖",
        "益",
        "桓",
        "公",
        "晋",
        "楚",
        "闫",
        "法",
        "汝",
        "鄢",
        "涂",
        "钦",
        "岳",
        "帅",
        "缑",
        "亢",
        "况",
        "郈",
        "有",
        "琴",
        "商",
        "牟",
        "佘",
        "佴",
        "伯",
        "赏",
        "墨",
        "哈",
        "谯",
        "笪",
        "年",
        "爱",
        "阳",
        "佟",
    }

    COMPOUND_SURNAMES: ClassVar[set[str]] = {
        "万俟",
        "司马",
        "上官",
        "欧阳",
        "夏侯",
        "诸葛",
        "闻人",
        "东方",
        "赫连",
        "皇甫",
        "尉迟",
        "公羊",
        "澹台",
        "公冶",
        "宗政",
        "濮阳",
        "淳于",
        "单于",
        "太叔",
        "申屠",
        "公孙",
        "仲孙",
        "轩辕",
        "令狐",
        "钟离",
        "宇文",
        "长孙",
        "慕容",
        "鲜于",
        "闾丘",
        "司徒",
        "司空",
        "亓官",
        "司寇",
        "子车",
        "颛孙",
        "端木",
        "巫马",
        "公西",
        "漆雕",
        "乐正",
        "壤驷",
        "公良",
        "拓跋",
        "夹谷",
        "宰父",
        "谷梁",
        "段干",
        "百里",
        "东郭",
        "南门",
        "呼延",
        "归海",
        "羊舌",
        "微生",
        "梁丘",
        "左丘",
        "东门",
        "西门",
        "南宫",
        "第五",
        "言",
        "福",
    }

    CONTEXT_WORDS: ClassVar[list[str]] = [
        "姓名",
        "名字",
        "叫",
        "是",
        "联系人",
        "负责人",
        "经办人",
        "收件人",
        "寄件人",
        "申请人",
        "被申请人",
        "原告",
        "被告",
        "证人",
        "受害人",
        "嫌疑人",
        "当事人",
        "业主",
        "租户",
        "房东",
        "买家",
        "卖家",
        "客户",
        "用户",
        "会员",
        "员工",
        "经理",
        "总监",
        "董事长",
        "总经理",
        "先生",
        "女士",
        "小姐",
        "name",
    ]

    NAME_BLACKLIST: ClassVar[set[str]] = {
        "北京市",
        "上海市",
        "天津市",
        "重庆市",
        "河北省",
        "山西省",
        "辽宁省",
        "吉林省",
        "黑龙江省",
        "江苏省",
        "浙江省",
        "安徽省",
        "福建省",
        "江西省",
        "山东省",
        "河南省",
        "湖北省",
        "湖南省",
        "广东省",
        "海南省",
        "四川省",
        "贵州省",
        "云南省",
        "陕西省",
        "甘肃省",
        "青海省",
        "台湾省",
        "自治区",
        "特别行政区",
        "高新区",
        "开发区",
        "工业园",
        "科技园",
        "有限公司",
        "股份公司",
        "集团公司",
        "责任公司",
        "分公司",
        "子公司",
        "办事处",
        "营业部",
        "事业部",
        "研究中心",
        "研究院",
        "研究所",
        "大学",
        "学院",
        "学校",
        "医院",
        "银行",
        "保险",
        "证券",
        "基金",
        "投资",
        "管理",
        "服务",
        "咨询",
        "科技",
        "网络",
        "信息",
        "数据",
        "软件",
        "硬件",
        "电子",
        "通信",
        "互联网",
        "物联网",
        "人工智能",
        "机器学习",
        "深度学习",
        "大数据",
        "云计算",
        "区块链",
    }

    def __init__(self, **kwargs: Any) -> None:
        """
        初始化姓名识别器

        Args:
            **kwargs: 其他参数传递给父类
        """
        super().__init__(
            supported_entities=["CN_NAME"],
            name="CN Name Recognizer",
            context=self.CONTEXT_WORDS,
            **kwargs,
        )
        self._all_surnames = self.COMMON_SURNAMES | self.COMPOUND_SURNAMES
        self._sorted_surnames = sorted(self._all_surnames, key=len, reverse=True)

    def analyze(
        self,
        text: str,
        entities: list[str],
        nlp_artifacts: NlpArtifacts | None,
    ) -> list[RecognizerResult]:
        """
        分析文本中的姓名

        优先使用NER结果，如果NER不可用则使用规则匹配。
        支持PaddleNLP LAC模型的NER结果格式。

        Args:
            text: 待分析的文本
            entities: 要识别的实体类型列表
            nlp_artifacts: NLP处理结果

        Returns:
            识别结果列表
        """
        results = []

        if nlp_artifacts:
            results = self._analyze_with_ner(text, nlp_artifacts)

        if not results:
            results = self._analyze_with_rules(text)

        return self._filter_results(text, results)

    def _analyze_with_ner(
        self,
        text: str,
        nlp_artifacts: NlpArtifacts,
    ) -> list[RecognizerResult]:
        """
        使用NER结果分析姓名

        支持两种格式：
        1. spaCy格式：nlp_artifacts.entities是spacy.tokens.Span列表
        2. PaddleNLP格式：nlp_artifacts.entities是字典列表

        Args:
            text: 原始文本
            nlp_artifacts: NLP处理结果

        Returns:
            识别结果列表
        """
        results = []

        if not hasattr(nlp_artifacts, "entities") or not nlp_artifacts.entities:
            return results

        for ent in nlp_artifacts.entities:
            if isinstance(ent, dict):
                if ent.get("label") in ("PERSON", "PER"):
                    name_text = ent.get("text", "")
                    start = ent.get("start", 0)
                    end = ent.get("end", len(name_text))
                    if self._validate_chinese_name(name_text):
                        score = self._calculate_score(name_text)
                        result = self._create_result(
                            entity_type="CN_NAME",
                            start=start,
                            end=end,
                            score=score,
                        )
                        results.append(result)
            elif hasattr(ent, "label_") and ent.label_ == "PERSON":
                name_text = text[ent.start_char : ent.end_char]
                if self._validate_chinese_name(name_text):
                    score = self._calculate_score(name_text)
                    result = self._create_result(
                        entity_type="CN_NAME",
                        start=ent.start_char,
                        end=ent.end_char,
                        score=score,
                    )
                    results.append(result)

        return results

    def _analyze_with_rules(self, text: str) -> list[RecognizerResult]:
        """
        使用规则匹配分析姓名

        Args:
            text: 原始文本

        Returns:
            识别结果列表
        """
        results = []

        for surname in self._sorted_surnames:
            start = 0
            while True:
                pos = text.find(surname, start)
                if pos == -1:
                    break

                name_end = self._find_name_end(text, pos, surname)
                name_text = text[pos:name_end]

                if self._validate_chinese_name(name_text):
                    score = self._calculate_score(name_text)
                    result = self._create_result(
                        entity_type="CN_NAME",
                        start=pos,
                        end=name_end,
                        score=score,
                    )
                    results.append(result)

                start = pos + 1

        return self._merge_overlapping_results(results)

    def _find_name_end(self, text: str, start: int, surname: str) -> int:
        """
        查找姓名结束位置

        Args:
            text: 原始文本
            start: 姓名开始位置
            surname: 姓氏

        Returns:
            姓名结束位置
        """
        surname_len = len(surname)
        max_name_len = 4
        end = start + surname_len

        while end < len(text) and end - start < max_name_len:
            char = text[end]
            if self._is_name_char(char):
                end += 1
            else:
                break

        return end

    def _is_name_char(self, char: str) -> bool:
        """
        判断字符是否可能是名字字符

        Args:
            char: 字符

        Returns:
            是否为名字字符
        """
        return "\u4e00" <= char <= "\u9fa5"

    def _validate_chinese_name(self, name: str) -> bool:
        """
        验证中文姓名有效性

        Args:
            name: 姓名字符串

        Returns:
            是否为有效姓名
        """
        if not name:
            return False

        if len(name) < 2 or len(name) > 4:
            return False

        if not all("\u4e00" <= c <= "\u9fa5" for c in name):
            return False

        has_surname = any(name.startswith(surname) for surname in self._sorted_surnames)

        if not has_surname:
            return False

        return all(blacklist_item not in name for blacklist_item in self.NAME_BLACKLIST)

    def _calculate_score(self, name: str) -> float:
        """
        计算姓名识别置信度

        Args:
            name: 姓名字符串

        Returns:
            置信度分数
        """
        score = 0.5

        for surname in self.COMPOUND_SURNAMES:
            if name.startswith(surname):
                score += 0.25
                break
        else:
            if name[0] in self.COMMON_SURNAMES:
                score += 0.15

        if len(name) == 3:
            score += 0.1
        elif len(name) == 2:
            score += 0.05

        if len(name) >= 3:
            given_name = name[1:] if name[0] in self.COMMON_SURNAMES else name[2:]
            if all("\u4e00" <= c <= "\u9fa5" for c in given_name):
                score += 0.1

        return min(score, 0.85)

    def _filter_results(
        self,
        text: str,
        results: list[RecognizerResult],
    ) -> list[RecognizerResult]:
        """
        过滤无效结果

        Args:
            text: 原始文本
            results: 识别结果列表

        Returns:
            过滤后的结果列表
        """
        filtered = []
        for result in results:
            name = text[result.start : result.end]
            if self._validate_chinese_name(name):
                filtered.append(result)
        return filtered

    def _merge_overlapping_results(
        self,
        results: list[RecognizerResult],
    ) -> list[RecognizerResult]:
        """
        合并重叠的结果，保留最高分数的结果

        Args:
            results: 识别结果列表

        Returns:
            合并后的结果列表
        """
        if not results:
            return []

        sorted_results = sorted(results, key=lambda r: (r.start, -r.score))

        merged = []
        for result in sorted_results:
            is_overlapping = False
            for existing in merged:
                if result.start >= existing.start and result.end <= existing.end:
                    is_overlapping = True
                    break
                if result.start < existing.end and result.end > existing.start:
                    if result.score > existing.score:
                        merged.remove(existing)
                    else:
                        is_overlapping = True
                    break

            if not is_overlapping:
                merged.append(result)

        return merged
