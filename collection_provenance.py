COLLECTION_MODES = {
    "BCorrect (FMM)": "api",
    "LanguageTool API": "api",
    "TextGears API": "api",
    "DeepL Write": "not reported",
    "Sapling Grammar Checker": "web_demo",
    "JSpell Free Web Checker": "web_demo",
    "Grammarly Free Grammar Checker": "web_demo",
}

COLLECTION_ROUTES = {
    "BCorrect (FMM)": "API",
    "LanguageTool API": "first-party API",
    "TextGears API": "RapidAPI gateway",
    "DeepL Write": "not reported",
    "Sapling Grammar Checker": "first-party web demo",
    "JSpell Free Web Checker": "first-party web checker",
    "Grammarly Free Grammar Checker": "first-party web demo",
}

COLLECTION_SOURCE_URLS = {
    "BCorrect (FMM)": "https://bcorrect-api.fly.dev/api/v1/check",
    "LanguageTool API": "https://api.languagetool.org/v2/check",
    "TextGears API": "https://textgears-textgears-v1.p.rapidapi.com/spelling",
    "DeepL Write": "not recorded",
    "Sapling Grammar Checker": "https://sapling.ai/grammar-check",
    "JSpell Free Web Checker": "https://www.jspell.com/checker/",
    "Grammarly Free Grammar Checker": "https://www.grammarly.com/grammar-check",
}

COLLECTION_LOCALES = {
    "BCorrect (FMM)": "not reported",
    "LanguageTool API": "en-US",
    "TextGears API": "en-US",
    "DeepL Write": "not reported",
    "Sapling Grammar Checker": "not reported",
    "JSpell Free Web Checker": "English (US)",
    "Grammarly Free Grammar Checker": "not reported",
}
