from decimal import Decimal, getcontext
getcontext().prec = 20  # 소수점 20자리까지 정밀도 확보

def initialize_arrays(count):
    return {
        'BIT_START_A50': [Decimal(0)] * count,
        'BIT_START_A100': [Decimal(0)] * count,
        'BIT_START_B50': [Decimal(0)] * count,
        'BIT_START_B100': [Decimal(0)] * count,
        'BIT_START_NBA100': [Decimal(0)] * count,
    }

def calculate_bit(nb, bit=Decimal('5.5'), reverse=False):
    nb = [Decimal(str(n)) for n in nb]
    if len(nb) < 2:
        return bit / Decimal(100)

    BIT_NB = Decimal(str(bit))
    max_val = max(nb)
    min_val = min(nb)
    COUNT = Decimal('50')
    CONT = Decimal('20')
    LEN = Decimal(str(len(nb)))

    negative_range = abs(min_val) if min_val < 0 else Decimal(0)
    positive_range = max_val if max_val > 0 else Decimal(0)

    increment_denom = COUNT * LEN - Decimal('1')
    negative_increment = negative_range / increment_denom if increment_denom != 0 else Decimal(0)
    positive_increment = positive_range / increment_denom if increment_denom != 0 else Decimal(0)

    total_slots = int(COUNT * len(nb))
    arrays = initialize_arrays(total_slots)

    count = Decimal(0)
    total_sum = Decimal(0)

    for value in nb:
        for _ in range(int(COUNT)):
            BIT_END = Decimal(1)
            inc = negative_increment if value < 0 else positive_increment

            A50 = min_val + inc * (count + Decimal(1))
            A100 = (count + Decimal(1)) * BIT_NB / (COUNT * LEN)

            B50 = A50 - inc * Decimal(2)
            B100 = A50 + inc
            NBA100 = A100 / (LEN - BIT_END) if (LEN - BIT_END) != 0 else Decimal(0)

            index = int(count)
            arrays['BIT_START_A50'][index] = A50
            arrays['BIT_START_A100'][index] = A100
            arrays['BIT_START_B50'][index] = B50
            arrays['BIT_START_B100'][index] = B100
            arrays['BIT_START_NBA100'][index] = NBA100

            count += Decimal(1)

        total_sum += value

    if reverse:
        arrays['BIT_START_NBA100'].reverse()

    NB50 = Decimal(0)
    for value in nb:
        for a in range(len(arrays['BIT_START_NBA100'])):
            if arrays['BIT_START_B50'][a] <= value <= arrays['BIT_START_B100'][a]:
                NB50 += arrays['BIT_START_NBA100'][a]
                break

    return bit - NB50 if len(nb) == 2 else NB50

SUPER_BIT = Decimal(0)

def update_super_bit(new_value):
    global SUPER_BIT
    SUPER_BIT = new_value

def BIT_MAX_NB(nb, bit=Decimal('5.5')):
    bit = Decimal(str(bit))
    result = calculate_bit(nb, bit, reverse=False)
    if not isinstance(result, Decimal) or not (Decimal(-100) <= result <= Decimal(100)):
        return SUPER_BIT
    update_super_bit(result)
    return result

def BIT_MIN_NB(nb, bit=Decimal('5.5')):
    bit = Decimal(str(bit))
    result = calculate_bit(nb, bit, reverse=True)
    if not isinstance(result, Decimal) or not (Decimal(-100) <= result <= Decimal(100)):
        return SUPER_BIT
    update_super_bit(result)
    return result

def word_nb_unicode_format(domain: str = ''):
    default_prefix = '안 녕 한 국 인 터 넷 . 한 국'
    domain = f"{default_prefix}:{domain}" if domain else default_prefix
    chars = list(domain)

    lang_ranges = [
        {'range': (0xAC00, 0xD7AF), 'prefix': 1000000},
        {'range': (0x3040, 0x309F), 'prefix': 2000000},
        {'range': (0x30A0, 0x30FF), 'prefix': 3000000},
        {'range': (0x4E00, 0x9FFF), 'prefix': 4000000},
        {'range': (0x0410, 0x044F), 'prefix': 5000000},
        {'range': (0x0041, 0x007A), 'prefix': 6000000},
        {'range': (0x0590, 0x05FF), 'prefix': 7000000},
        {'range': (0x00C0, 0x00FD), 'prefix': 8000000},
        {'range': (0x0E00, 0x0E7F), 'prefix': 9000000},
    ]

    result = []
    for char in chars:
        unicode_value = ord(char)
        matched_lang = next((lang for lang in lang_ranges if lang['range'][0] <= unicode_value <= lang['range'][1]), None)
        prefix = matched_lang['prefix'] if matched_lang else 0
        result.append(Decimal(prefix + unicode_value))

    return result

def similarity_score(a, b):
    a = Decimal(a)
    b = Decimal(b)
    if a == b:
        return Decimal('1.0')
    max_val = max(abs(a), abs(b), Decimal('1e-9'))
    diff = abs(a - b)
    score = Decimal('1') - (diff / max_val)
    return score.quantize(Decimal('1.0000000000'))

def find_similar_post_id(rss_items, target_title, threshold=Decimal('0.98')):
    target_vec = word_nb_unicode_format(target_title)
    target_bit = BIT_MAX_NB(target_vec)

    print(f"\n🎯 기준 제목: {target_title}")
    print(f"🧠 기준 BIT_MAX_NB 값: {target_bit}")
    print("📋 RSS 제목별 유사도 목록 ↓\n")

    best_match = None
    best_title = None
    highest_score = Decimal(0)

    for item in rss_items:
        rss_title = item.title.text.strip()
        rss_vec = word_nb_unicode_format(rss_title)
        rss_bit = BIT_MAX_NB(rss_vec)

        score = similarity_score(target_bit, rss_bit)

        # print(f"📝 RSS 제목: {rss_title}")
        # print(f"🔢 RSS BIT_MAX_NB: {rss_bit} | 유사도: {score}")

        if score >= threshold and score > highest_score:
            best_match = item.link.text.strip().split('/')[-1].split('?')[0]
            best_title = rss_title
            highest_score = score
            print("✅ [일치 후보] 선택됨 ↓")
            print(f"📝 RSS 제목       : {rss_title}")
            print(f"🔢 RSS BIT_MAX_NB : {rss_bit}")
            print(f"📈 유사도         : {score}")
            print(f"🆚 기준 BIT 값    : {target_bit}")
            print(f"🆚 매칭 BIT 값    : {rss_bit}")
            print("-" * 60)

    if best_match:
        print("\n🏁 최종 매칭 결과 ↓")
        print(f"🔎 기준 제목            : {target_title}")
        print(f"🔍 매칭된 RSS 제목     : {best_title}")
        print(f"🧠 기준 BIT_MAX_NB 값  : {target_bit}")
        print(f"🧠 매칭 BIT_MAX_NB 값  : {BIT_MAX_NB(word_nb_unicode_format(best_title))}")
        print(f"📈 최종 유사도 점수     : {highest_score}")
        print(f"🆔 최종 선택된 post_id : {best_match}")
        print("-" * 60)
    else:
        print("\n❌ 기준 이상 유사도 제목이 없음")
        print(f"🔎 기준 제목            : {target_title}")
        print(f"🧠 기준 BIT_MAX_NB 값  : {target_bit}")
        print(f"📉 유사도 임계값       : {threshold}")
        print("-" * 60)


    return best_match
