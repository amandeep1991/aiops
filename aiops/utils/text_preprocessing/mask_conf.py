timezones_matching_regex = r"\b(hst|akdt|akst|pst|pdt|mdt|mst|cdt|cst|edt|pet|est|cot|adt|ast|clt|clst|art|brst|brt|gmt|wet|bst|west|utc|cest|wat|cet|cat|msd|eat|irst|msk|eet|eest|gst|ist|pkt|bdt|wit|ict|sgt|hkt|pht|kst|jst|nzdt|nzst)\b"
months_matching_regex = r"\b(january|february|march|april|may|june|july|august|september|october|november|december|jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\b"


mask_map = {
    "mask_months": (months_matching_regex, "month"),
    "mask_timezones": (timezones_matching_regex, "time"),
    "mask_years": (r'\b((?<=(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec))|(?<=(june|july))|(?<=(march|april))|(?<=(august))|(?<=(january|october))|(?<=(february|november|december))|(?<=(september)))\b[, ]*\d{2,4}', " year"),
    "mask_email_ids": (r'[\(\<\[]*(mailto *\:)*(Email)*[\s\n]*[\(\<\[]*[a-z0-9]+[\._]?[a-z0-9\.]+[@](\w+)[.]\w{2,3}[\]\>\)]*', r" email "),
    # "mask_email_ids": (r'[\(\<]*(mailto *\:)*[\(\<]*[a-z0-9]+[\._]?[a-z0-9\.]+[@](\w+)[.]\w{2,3}[\>\)]*', r"\2 email"),
    "mask_mentions": (r'\b[@][\w_-]+\b', r" person"),
    "mask_ips": (r'\b(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}|[\w\d]{2}:[\w\d]{2}:[\w\d]{2}:[\w\d]{2}:[\w\d]{2}:[\w\d]{2})\b', r"ip"),
    "mask_paths": (r"(/[^/ ]*)+/?", r" path "),
    "mask_question_marks": (r"\?", r" question mark "),
    "mask_exclamation_marks": (r"\!", r" exclamation mark "),

}
