import re, os
tmp = os.environ["TEMP"]

def raw(p):
    return open(os.path.join(tmp, p), encoding="utf-8", errors="ignore").read()

# Hindu topic page: any .ece article links at all?
s = raw("th_topic_vellore.html")
ece = sorted(set(re.findall(r'href="(https://www\.thehindu\.com/[^"]+\.ece)"', s)))
print("hindu .ece links:", len(ece))
for l in ece[:10]:
    print("   ", l)

# DT city page: what href shapes exist?
s = raw("dt_city_vellore.html")
hrefs = re.findall(r'href="([^"]+)"', s)
story = sorted({h for h in hrefs if re.search(r"(vellore|katpadi|gudiyatham|ambur|ranipet|tirupattur|sholingur)", h, re.I)})
print("\ndt city vellore-ish hrefs:", len(story))
for h in story[:12]:
    print("   ", h[:110])

# DT archive sitemap depth + vellore yield for two sample years
for name in ("dt_d2017.xml", "dt_d2020.xml", "dt_d2022.xml"):
    p = os.path.join(tmp, name)
    if not os.path.exists(p):
        print(f"\n{name}: not fetched"); continue
    u = re.findall(r"<loc>(.*?)</loc>", raw(name))
    vel = [x for x in u if re.search(
        r"(vellore|katpadi|gudiyatham|pernambut|ambur|vaniyambadi|tirupattur|jolarpet|natrampalli|sholingur|walajapet|ranipet|arcot|melvisharam|arakkonam)", x, re.I)]
    print(f"\n{name}: urls={len(u)} vellore-region={len(vel)}")
    for x in vel[:10]:
        print("   ", x[:120])