#!/usr/bin/env python3
"""
営業一次提案 マルチエージェントシステム — デモ用モックアップ (Pattern C)
実行: python3 -m streamlit run app.py
"""

import os
import time
import datetime
import json
import base64
import streamlit as st
from google.oauth2 import service_account
from googleapiclient.discovery import build

# ─────────────────────────────────────────────────────────────────────────────
# GOOGLE SLIDES CONFIGURATION
# ─────────────────────────────────────────────────────────────────────────────
TEMPLATE_ID  = '1XcGIsUwqIILONE10i-wDH-gfrJE17UnzHBUNCFXTo4Q'
W, H         = 9144000, 5143500
HDR_Y, SEP_Y, CT_Y = 610000, 1390000, 1460000
FONT = 'M PLUS 1p'
SCOPES = ['https://www.googleapis.com/auth/presentations',
          'https://www.googleapis.com/auth/drive']

# カラーパレット（plain dict — v3 準拠）
BLUE       = {'red': 0.259, 'green': 0.522, 'blue': 0.957}
TEAL       = {'red': 0.00,  'green': 0.592, 'blue': 0.655}
ORANGE     = {'red': 1.00,  'green': 0.671, 'blue': 0.251}
BLACK      = {'red': 0.00,  'green': 0.00,  'blue': 0.00}
DARK_GRAY  = {'red': 0.349, 'green': 0.349, 'blue': 0.349}
LIGHT_GRAY = {'red': 0.933, 'green': 0.933, 'blue': 0.933}
BLUE_LIGHT = {'red': 0.898, 'green': 0.922, 'blue': 0.996}


def get_service_account_credentials():
    """サービスアカウントの認証情報を取得"""
    try:
        # Streamlit Cloudの場合はsecretsから取得
        if "service_account" in st.secrets:
            credentials = service_account.Credentials.from_service_account_info(
                st.secrets["service_account"],
                scopes=SCOPES
            )
        # Base64エンコードされたキーから取得
        elif "service_account_base64" in st.secrets:
            decoded = base64.b64decode(st.secrets["service_account_base64"])
            service_account_info = json.loads(decoded)
            credentials = service_account.Credentials.from_service_account_info(
                service_account_info,
                scopes=SCOPES
            )
        # ローカル環境の場合はファイルから取得
        elif os.path.exists("service-account-key.json"):
            credentials = service_account.Credentials.from_service_account_file(
                "service-account-key.json",
                scopes=SCOPES
            )
        else:
            st.error("❌ サービスアカウントの認証情報が見つかりません")
            return None

        return credentials
    except Exception as e:
        st.error(f"❌ 認証エラー: {e}")
        return None


def _svc():
    """Google API サービスを初期化"""
    creds = get_service_account_credentials()
    if not creds:
        st.error("認証に失敗しました")
        st.stop()

    s = build('slides', 'v1', credentials=creds, cache_discovery=False)
    d = build('drive',  'v3', credentials=creds, cache_discovery=False)
    return s, d


# ── v3 準拠ヘルパー関数 ─────────────────────────────────────────────
def fc(c):  return {'rgbColor': c}
def tc(c):  return {'opaqueColor': {'rgbColor': c}}
def sf(c):  return {'solidFill': {'color': fc(c)}}


def rect(reqs, sid, oid, x, y, w, h, bg=None, border_c=None, border_w=0):
    reqs.append({'createShape': {
        'objectId': oid, 'shapeType': 'RECTANGLE',
        'elementProperties': {'pageObjectId': sid,
            'size': {'width': {'magnitude': w, 'unit': 'EMU'},
                     'height': {'magnitude': h, 'unit': 'EMU'}},
            'transform': {'scaleX': 1, 'scaleY': 1,
                          'translateX': x, 'translateY': y, 'unit': 'EMU'}}}})
    sp = {'shapeBackgroundFill': sf(bg) if bg else {'propertyState': 'NOT_RENDERED'}}
    sp['outline'] = ({'outlineFill': sf(border_c), 'weight': {'magnitude': border_w, 'unit': 'PT'}}
                     if border_c and border_w else {'propertyState': 'NOT_RENDERED'})
    reqs.append({'updateShapeProperties': {'objectId': oid,
                  'shapeProperties': sp, 'fields': 'shapeBackgroundFill,outline'}})


def textbox(reqs, sid, oid, text, x, y, w, h,
            size=12, bold=False, color=BLACK, align='START',
            bg=None, border_c=None, border_w=0, ls=None, sa=0):
    reqs.append({'createShape': {
        'objectId': oid, 'shapeType': 'TEXT_BOX',
        'elementProperties': {'pageObjectId': sid,
            'size': {'width': {'magnitude': w, 'unit': 'EMU'},
                     'height': {'magnitude': h, 'unit': 'EMU'}},
            'transform': {'scaleX': 1, 'scaleY': 1,
                          'translateX': x, 'translateY': y, 'unit': 'EMU'}}}})
    sp = {'shapeBackgroundFill': sf(bg) if bg else {'propertyState': 'NOT_RENDERED'}}
    sp['outline'] = ({'outlineFill': sf(border_c), 'weight': {'magnitude': border_w, 'unit': 'PT'}}
                     if border_c and border_w else {'propertyState': 'NOT_RENDERED'})
    reqs.append({'updateShapeProperties': {'objectId': oid,
                  'shapeProperties': sp, 'fields': 'shapeBackgroundFill,outline'}})
    reqs.append({'insertText': {'objectId': oid, 'text': text}})
    ts = {'bold': bold, 'fontSize': {'magnitude': size, 'unit': 'PT'},
          'fontFamily': FONT, 'foregroundColor': tc(color)}
    reqs.append({'updateTextStyle': {'objectId': oid, 'style': ts,
                  'fields': 'bold,fontSize,fontFamily,foregroundColor'}})
    ps = {'alignment': align, 'spaceAbove': {'magnitude': sa, 'unit': 'PT'}}
    if ls: ps['lineSpacing'] = ls
    reqs.append({'updateParagraphStyle': {'objectId': oid, 'style': ps,
                  'fields': 'alignment,spaceAbove' + (',lineSpacing' if ls else '')}})


def header(reqs, sid, prefix, title):
    textbox(reqs, sid, f'{prefix}_ttl', title,
            150000, HDR_Y, W - 300000, 155000, size=20, bold=False, color=BLACK)
    rect(reqs, sid, f'{prefix}_sep', 150000, SEP_Y, W - 300000, 8000, bg=LIGHT_GRAY)


def _flush(svc, pid, reqs):
    if reqs:
        svc.presentations().batchUpdate(presentationId=pid, body={'requests': reqs}).execute()
    time.sleep(2)


def share_presentation(drive_service, presentation_id):
    """プレゼンテーションを共有設定"""
    try:
        # リンクを知っている全員が編集可能に設定
        permission = {
            'type': 'anyone',
            'role': 'writer',
        }
        drive_service.permissions().create(
            fileId=presentation_id,
            body=permission,
            fields='id'
        ).execute()
        return True
    except Exception as e:
        # ドメインポリシーで制限されている場合はスキップ
        return False


def generate_proposal_slides(client_name, industry, budget, timing, kpi_list):
    svc, drive = _svc()

    # Copy template & share
    today = datetime.date.today().strftime('%Y.%m.%d')
    kpi_str_short = ' / '.join(kpi_list[:2]) if kpi_list else 'CV最大化'
    slide_title = f'{timing} {industry}向け SmartNews 広告活用ご提案'
    file_name = f'{today} {client_name} 御中 {slide_title}'
    pid = drive.files().copy(fileId=TEMPLATE_ID,
        body={'name': file_name}, fields='id').execute()['id']

    pres  = svc.presentations().get(presentationId=pid).execute()
    slides = pres['slides']

    # ── Title slide (index 0): キーマッチで3フィールドを個別差し替え ──
    slide_title_multiline = f'{timing} {industry}向け\nSmartNews 広告活用ご提案'
    REPLACEMENTS = {
        '社名 御中':    (f'{client_name} 御中',  None,  None),
        '2022.01.05':  (today,                    6,     DARK_GRAY),
        '資料タイトル': (slide_title_multiline,      22,    BLACK),
    }
    s0 = slides[0]
    reqs = []
    for e in s0.get('pageElements', []):
        shape = e.get('shape', {})
        if not shape or not shape.get('text'):
            continue
        te   = shape['text'].get('textElements', [])
        text = ''.join(t.get('textRun', {}).get('content', '') for t in te if 'textRun' in t)
        oid  = e['objectId']
        for key, (new_text, font_size, color) in REPLACEMENTS.items():
            if key in text:
                reqs.append({'deleteText': {'objectId': oid, 'textRange': {'type': 'ALL'}}})
                if new_text:
                    reqs.append({'insertText': {'objectId': oid, 'text': new_text, 'insertionIndex': 0}})
                    if font_size:
                        reqs.append({'updateTextStyle': {
                            'objectId': oid,
                            'style': {'fontFamily': FONT, 'bold': False,
                                      'fontSize': {'magnitude': font_size, 'unit': 'PT'},
                                      'foregroundColor': tc(color)},
                            'fields': 'fontFamily,bold,fontSize,foregroundColor',
                            'textRange': {'type': 'ALL'},
                        }})
                break
    _flush(svc, pid, reqs)

    # Delete slides 2〜end from template (keep only title)
    pres   = svc.presentations().get(presentationId=pid).execute()
    slides = pres['slides']
    del_reqs = [{'deleteObject': {'objectId': s['objectId']}} for s in reversed(slides[1:])]
    if del_reqs:
        _flush(svc, pid, del_reqs)

    pres   = svc.presentations().get(presentationId=pid).execute()
    slides = pres['slides']
    kpi_str = ' / '.join(kpi_list) if kpi_list else 'CV最大化 / CPA改善'

    SLIDE_DEFS = [
        ('SmartNews をおすすめする理由', [
            ('リーチ力',      BLUE,   '国内月間 2,000万ユーザー（35〜54歳の購買力層中心）\n独自スマートチャネル技術で高品質ユーザーを確保'),
            ('計測精度',      BLUE,   'ITP対応済みコンバージョン API で精度の高い CV 計測\n統計モデリングによる補完で計測損失を最小化'),
            ('実績',          BLUE,   '類似業種平均: CPA -28% / CV +41%\n春商戦期の広告効果最大化に豊富な知見'),
        ]),
        (f'推奨活用プラン  /  KPI: {kpi_str}', [
            ('① 検索広告 — 指名 + 競合指名',  TEAL,   '月予算: ¥2,000万　指名CVシェア +15pt / CPA 現状維持\n競合入札に対抗し、ブランドワードを守る'),
            ('② ショッピング広告',             TEAL,   '月予算: ¥1,500万　CV最大化 → 3週後にtCPA移行\nCV≥150件/月 達成後に移行。EC強化戦略と合致'),
            ('③ 動画広告（YouTube）',          TEAL,   '月予算: ¥800万　在庫残 18%（3/20 までの確保を推奨）\nブランドリフト計測付き'),
        ]),
        ('具体的な成果事例', [
            ('事例 1 — 小売EC（類似業種）',  BLUE,   '施策: ブランド検索 × リターゲティング\n成果: CPA -28%、CV +41%。春商戦期に集中投下'),
            ('事例 2 — アパレル通販',        BLUE,   '施策: 動画 × ショッピング広告\n成果: ROAS +35%。ブランドリフト計測で認知向上も確認'),
            ('事例 3 — 家電量販',            BLUE,   '施策: 指名 + 競合指名広告\n成果: 指名CVシェア +19pt。競合参入後も自社シェアを維持'),
        ]),
        ('発注・配信スケジュール', [
            ('3/20（木）締め切り',  ORANGE, '予算・施策の最終確認 → 発注書受領\n動画在庫確保の期限（残18%のため早期決断が必要）'),
            ('3/25（火）',          ORANGE, 'クリエイティブ・入稿データ受領\nキャンペーン設定・審査開始'),
            ('4/1（水）配信開始',   ORANGE, '週次レポート提供開始\n3週後に tCPA 移行判断を実施'),
        ]),
        ('顧客確認事項', [
            ('① 春季キャンペーン予算の上限',     DARK_GRAY, '推奨: 月次 ¥4,300万（検索+ショッピング+動画）\n代替: ¥2,000万の検索のみでスタートし効果確認後に拡大'),
            ('② 競合指名施策の社内可否',          DARK_GRAY, '法務確認が必要な場合は 3/10 までにご回答ください\nNG の場合: 自社指名防衛プランに切り替えます'),
            ('③ 3/20 キャンペーン設定完了の可否', DARK_GRAY, '4/1 配信開始に向けた必達締め切りです\n動画在庫確保のため本日中のご確認をお願いします'),
        ]),
    ]

    for sdef_title, blocks in SLIDE_DEFS:
        # Duplicate last slide
        last_sid = slides[-1]['objectId']
        svc.presentations().batchUpdate(presentationId=pid,
            body={'requests': [{'duplicateObject': {'objectId': last_sid}}]}).execute()
        time.sleep(1)
        pres   = svc.presentations().get(presentationId=pid).execute()
        slides = pres['slides']
        new_slide = slides[-1]
        new_sid   = new_slide['objectId']

        # Delete existing elements
        del_reqs = [{'deleteObject': {'objectId': e['objectId']}} for e in new_slide.get('pageElements', [])]
        if del_reqs:
            svc.presentations().batchUpdate(presentationId=pid, body={'requests': del_reqs}).execute()

        # Build content
        p    = f's{len(slides)}'
        reqs = []
        header(reqs, new_sid, p, sdef_title)
        y = CT_Y

        for i, (label, color, body) in enumerate(blocks):
            lh = 340000
            bh = max((body.count('\n') + 1) * 230000 + 120000, 380000)

            # 左アクセントバー + ラベル
            rect(reqs, new_sid, f'{p}_bar{i}', 120000, y, 8000, lh, bg=color)
            textbox(reqs, new_sid, f'{p}_l{i}', label,
                    180000, y, W - 330000, lh, size=14, color=color)
            y += lh + 10000

            # 本文
            textbox(reqs, new_sid, f'{p}_b{i}', body,
                    180000, y, W - 330000, bh, size=12, color=DARK_GRAY, ls=165)
            y += bh + 60000

        _flush(svc, pid, reqs)

    # 共有設定
    share_presentation(drive, pid)

    return f'https://docs.google.com/presentation/d/{pid}/edit', pid


# ─────────────────────────────────────────────────────────────────────────────
# STREAMLIT APP
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="営業 AI Agent System",
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# session_state 初期化
for k, v in [('agents_done', False), ('slides_url', None), ('client_info', {})]:
    if k not in st.session_state:
        st.session_state[k] = v

# ─────────────────────────────────────────────────────────────────────────────
# DESIGN SYSTEM  ―  すべてのスタイルをCSSクラスで定義
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@700;800&family=Manrope:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;500&display=swap');

:root {
  --bg:     #07091A;
  --s1:     #0D1428;
  --s2:     #131C35;
  --s3:     #1A2540;
  --bd:     rgba(79,142,247,0.14);
  --bd2:    rgba(79,142,247,0.26);
  --blue:   #4F8EF7;
  --teal:   #2EC4B6;
  --amber:  #F4A261;
  --green:  #34D399;
  --gray-c: #8A8EA0;
  --text:   #C8D4EE;
  --muted:  #4E5E7E;
  --white:  #F0F4FF;
  --font:   'Manrope','Hiragino Sans','Yu Gothic',sans-serif;
  --mono:   'IBM Plex Mono',monospace;
  --head:   'Syne','Hiragino Sans',sans-serif;
}

/* ── Global ──────────────────────────────────────── */
html,body,.stApp { background:var(--bg) !important; color:var(--text) !important; }
.stApp > header,[data-testid="stToolbar"],[data-testid="stDecoration"],[data-testid="stStatusWidget"] { display:none !important; }
.block-container { padding:2rem 3rem 4rem !important; max-width:1160px !important; margin:0 auto !important; }
* { font-family:var(--font) !important; }
h1,h2,h3 { font-family:var(--head) !important; color:var(--white) !important; }
hr { border-color:var(--bd) !important; margin:1.6rem 0 !important; }
::-webkit-scrollbar { width:4px; }
::-webkit-scrollbar-track { background:var(--bg); }
::-webkit-scrollbar-thumb { background:var(--s3); border-radius:4px; }

/* ── Labels ──────────────────────────────────────── */
label,.stSelectbox label,.stTextInput label,.stTextArea label,.stMultiSelect label {
  color:var(--muted) !important; font-size:10px !important; font-weight:700 !important;
  letter-spacing:0.12em !important; text-transform:uppercase !important; font-family:var(--mono) !important;
}

/* ── Inputs ──────────────────────────────────────── */
.stTextInput > div > div > input,
.stTextArea > div > div > textarea {
  background:var(--s2) !important; border:1px solid var(--bd2) !important;
  border-radius:8px !important; color:var(--text) !important; font-size:14px !important;
}
.stTextInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus {
  border-color:var(--blue) !important; box-shadow:0 0 0 3px rgba(79,142,247,0.18) !important;
}
.stTextInput > div > div > input::placeholder,
.stTextArea > div > div > textarea::placeholder { color:var(--muted) !important; }

/* ── Selectbox ───────────────────────────────────── */
.stSelectbox > div > div { background:var(--s2) !important; border:1px solid var(--bd2) !important; border-radius:8px !important; color:var(--text) !important; }
.stSelectbox svg { fill:var(--muted) !important; }

/* ── Multiselect ─────────────────────────────────── */
.stMultiSelect > div > div { background:var(--s2) !important; border:1px solid var(--bd2) !important; border-radius:8px !important; }
.stMultiSelect span[data-baseweb="tag"] { background:rgba(79,142,247,0.18) !important; color:var(--blue) !important; border:1px solid rgba(79,142,247,0.3) !important; border-radius:4px !important; }

/* ── Submit button ───────────────────────────────── */
.stFormSubmitButton > button {
  background:linear-gradient(135deg,#1E3A8A,#2563EB) !important;
  color:#fff !important; border:none !important; border-radius:10px !important;
  font-weight:700 !important; font-size:15px !important; letter-spacing:0.06em !important;
  box-shadow:0 4px 28px rgba(30,58,138,0.5),0 0 0 1px rgba(79,142,247,0.2) !important;
  transition:all 0.2s !important;
}
.stFormSubmitButton > button:hover { transform:translateY(-2px) !important; box-shadow:0 8px 36px rgba(30,58,138,0.7) !important; }

/* ── st.status ───────────────────────────────────── */
[data-testid="stStatusContainer"] { background:var(--s1) !important; border:1px solid var(--bd2) !important; border-radius:10px !important; margin:6px 0 !important; }
[data-testid="stStatusContainer"] summary { color:var(--text) !important; font-size:13px !important; }
[data-testid="stStatusContainerBody"] { background:var(--s1) !important; }
[data-testid="stExpanderToggleIcon"] { color:var(--muted) !important; }

/* ── Markdown content ────────────────────────────── */
.stMarkdown p  { color:var(--text) !important; line-height:1.75; font-size:13px; }
.stMarkdown li { color:var(--text) !important; font-size:13px; }
.stMarkdown strong { color:var(--white) !important; }
.stMarkdown blockquote { border-left:3px solid var(--blue) !important; background:var(--s2) !important; padding:6px 14px !important; border-radius:0 6px 6px 0 !important; margin:6px 0 !important; }
.stMarkdown blockquote p { color:var(--muted) !important; font-size:12px; }
.stMarkdown table { width:100%; border-collapse:collapse; margin:8px 0; }
.stMarkdown th { background:var(--s3) !important; color:var(--muted) !important; font-size:10px !important; text-transform:uppercase; letter-spacing:0.08em; padding:8px 12px !important; border:1px solid var(--bd) !important; font-family:var(--mono) !important; }
.stMarkdown td { color:var(--text) !important; font-size:13px !important; padding:8px 12px !important; border:1px solid var(--bd) !important; background:var(--s1) !important; }
.stMarkdown code { background:var(--s3) !important; color:var(--teal) !important; border-radius:4px !important; padding:2px 6px !important; font-family:var(--mono) !important; font-size:12px !important; }

/* ── Metrics ─────────────────────────────────────── */
[data-testid="stMetric"] { background:var(--s1) !important; border:1px solid var(--bd2) !important; border-radius:12px !important; padding:1.4rem 1.6rem !important; }
[data-testid="stMetricLabel"] { color:var(--muted) !important; font-size:10px !important; text-transform:uppercase; letter-spacing:0.1em; font-family:var(--mono) !important; }
[data-testid="stMetricValue"] { color:var(--white) !important; font-size:2rem !important; font-weight:700 !important; font-family:var(--head) !important; }

/* ── Alerts ──────────────────────────────────────── */
.stSuccess { background:rgba(52,211,153,0.07) !important; border:1px solid rgba(52,211,153,0.22) !important; border-radius:10px !important; }
.stSuccess p,.stSuccess div { color:var(--green) !important; }
.stWarning { background:rgba(244,162,97,0.07) !important; border:1px solid rgba(244,162,97,0.22) !important; border-radius:10px !important; }
.stCaption,small { color:var(--muted) !important; font-size:12px !important; }

/* ── Hero block ──────────────────────────────────── */
.hero {
  position:relative; overflow:hidden; border-radius:16px;
  padding:36px 44px 32px; margin-bottom:28px;
  background:linear-gradient(135deg,#0D1428 0%,#0A1020 60%,#0F1A38 100%);
  border:1px solid rgba(79,142,247,0.15);
}
.hero-grid {
  position:absolute; inset:0; pointer-events:none;
  background-image:linear-gradient(rgba(79,142,247,0.035) 1px,transparent 1px),linear-gradient(90deg,rgba(79,142,247,0.035) 1px,transparent 1px);
  background-size:44px 44px;
}
.hero-glow {
  position:absolute; top:-80px; right:-80px; width:360px; height:360px;
  background:radial-gradient(circle,rgba(79,142,247,0.10) 0%,transparent 65%);
  pointer-events:none;
}
.hero-inner { position:relative; z-index:1; }
.hero-eyebrow { display:flex; align-items:center; gap:10px; margin-bottom:18px; }
.hero-label { font-family:var(--mono) !important; font-size:10px; letter-spacing:0.18em; text-transform:uppercase; color:rgba(79,142,247,0.55); }
.hero-title { font-family:var(--head) !important; font-size:2.5rem; font-weight:800; line-height:1.1; color:#F0F4FF; margin:0 0 10px 0; letter-spacing:-0.02em; }
.hero-accent { color:#4F8EF7; }
.hero-sub { color:rgba(200,212,238,0.45); font-size:13px; margin:0 0 28px 0; letter-spacing:0.01em; }

/* ── Architecture flow ───────────────────────────── */
.arch-flow { display:flex; align-items:center; gap:6px; flex-wrap:wrap; }
.arch-node { border-radius:6px; padding:4px 12px; font-size:11px; font-weight:700; font-family:var(--mono) !important; }
.arch-blue  { background:rgba(79,142,247,0.12); border:1px solid rgba(79,142,247,0.28); color:#4F8EF7; }
.arch-teal  { background:rgba(46,196,182,0.10); border:1px solid rgba(46,196,182,0.25); color:#2EC4B6; }
.arch-amber { background:rgba(244,162,97,0.10); border:1px solid rgba(244,162,97,0.28); color:#F4A261; }
.arch-gray  { background:rgba(138,142,160,0.10); border:1px solid rgba(138,142,160,0.22); color:#8A8EA0; }
.arch-arrow { color:rgba(200,212,238,0.18); font-size:14px; }

/* ── Section header ──────────────────────────────── */
.phase-row { display:flex; align-items:center; gap:12px; margin:28px 0 10px; }
.phase-num {
  width:26px; height:26px; border-radius:6px; display:flex; align-items:center; justify-content:center;
  font-family:var(--mono) !important; font-size:11px; font-weight:700;
}
.phase-num-blue  { background:rgba(79,142,247,0.15);  border:1px solid rgba(79,142,247,0.35);  color:#4F8EF7; }
.phase-num-teal  { background:rgba(46,196,182,0.15);  border:1px solid rgba(46,196,182,0.35);  color:#2EC4B6; }
.phase-num-amber { background:rgba(244,162,97,0.15);  border:1px solid rgba(244,162,97,0.38);  color:#F4A261; }
.phase-num-gray  { background:rgba(138,142,160,0.15); border:1px solid rgba(138,142,160,0.35); color:#8A8EA0; }
.phase-title { font-family:var(--head) !important; font-size:15px; font-weight:700; color:#F0F4FF; letter-spacing:0.01em; }
.phase-sub { color:rgba(200,212,238,0.30); font-size:11px; font-weight:400; margin-left:4px; }
.phase-line { flex:1; height:1px; background:rgba(79,142,247,0.10); margin-left:4px; }

/* ── Agent output header chip ────────────────────── */
.agent-chip { display:inline-flex; align-items:center; gap:7px; border-radius:6px; padding:4px 12px; margin-bottom:10px; }
.chip-blue  { background:rgba(79,142,247,0.10);  border:1px solid rgba(79,142,247,0.22); }
.chip-teal  { background:rgba(46,196,182,0.10);  border:1px solid rgba(46,196,182,0.22); }
.chip-amber { background:rgba(244,162,97,0.10);  border:1px solid rgba(244,162,97,0.22); }
.chip-gray  { background:rgba(138,142,160,0.10); border:1px solid rgba(138,142,160,0.20); }
.chip-dot { width:5px; height:5px; border-radius:50%; }
.chip-dot-blue  { background:#4F8EF7; box-shadow:0 0 6px #4F8EF7; }
.chip-dot-teal  { background:#2EC4B6; box-shadow:0 0 6px #2EC4B6; }
.chip-dot-amber { background:#F4A261; box-shadow:0 0 6px #F4A261; }
.chip-dot-gray  { background:#8A8EA0; box-shadow:0 0 6px #8A8EA0; }
.chip-label { font-family:var(--mono) !important; font-size:10px; font-weight:700; letter-spacing:0.10em; text-transform:uppercase; }
.chip-label-blue  { color:#4F8EF7; }
.chip-label-teal  { color:#2EC4B6; }
.chip-label-amber { color:#F4A261; }
.chip-label-gray  { color:#8A8EA0; }

/* ── Section label ───────────────────────────────── */
.section-eyebrow { font-family:var(--mono) !important; font-size:10px; font-weight:700; letter-spacing:0.15em; text-transform:uppercase; color:rgba(79,142,247,0.55); margin-bottom:14px; }

/* ── Next steps card ─────────────────────────────── */
.next-card { background:var(--s1); border:1px solid rgba(79,142,247,0.15); border-radius:10px; padding:18px 22px; }
.next-eyebrow { font-family:var(--mono) !important; font-size:10px; letter-spacing:0.12em; text-transform:uppercase; color:rgba(79,142,247,0.45); margin-bottom:12px; }
.next-actions { display:flex; gap:12px; flex-wrap:wrap; }
.next-btn { border-radius:7px; padding:8px 16px; font-size:13px; font-weight:600; }
.next-btn-blue  { background:rgba(79,142,247,0.10); border:1px solid rgba(79,142,247,0.22); color:#4F8EF7; }
.next-btn-teal  { background:rgba(46,196,182,0.08); border:1px solid rgba(46,196,182,0.20); color:#2EC4B6; }
.next-btn-gray  { background:rgba(138,142,160,0.08); border:1px solid rgba(138,142,160,0.18); color:#8A8EA0; }

/* ── Button style override ───────────────────────── */
.stButton > button {
  background:linear-gradient(135deg,#1E3A8A,#2563EB) !important;
  color:#fff !important; border:none !important; border-radius:10px !important;
  font-weight:700 !important; font-size:15px !important; letter-spacing:0.06em !important;
  box-shadow:0 4px 28px rgba(30,58,138,0.5),0 0 0 1px rgba(79,142,247,0.2) !important;
  transition:all 0.2s !important;
}
.stButton > button:hover { transform:translateY(-2px) !important; box-shadow:0 8px 36px rgba(30,58,138,0.7) !important; }

/* ── Expander ────────────────────────────────────── */
.streamlit-expanderHeader { background:var(--s1) !important; border:1px solid var(--bd2) !important; border-radius:10px !important; color:var(--text) !important; }
.streamlit-expanderContent { background:var(--s1) !important; border:1px solid var(--bd2) !important; border-top:none !important; border-radius:0 0 10px 10px !important; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# HERO HEADER  ― クラス名のみ使用、インラインstyle なし
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="hero">
<div class="hero-grid"></div>
<div class="hero-glow"></div>
<div class="hero-inner">
<div class="hero-eyebrow">
<img src="https://help-ads.smartnews.com/wp-content/themes/help/img/logo.png?1771980452" alt="SmartNews" style="height:36px;width:auto;flex-shrink:0;">
<img src="https://help-ads.smartnews.com/wp-content/themes/help/img/site-title.svg?1771980452" alt="SmartNews Ads" style="height:18px;width:auto;flex-shrink:0;filter:brightness(0) invert(1);">
<span style="color:rgba(200,212,238,0.18);font-size:12px;margin:0 6px;">|</span>
<span class="hero-label">営業一次提案 AI SYSTEM &nbsp;·&nbsp; PATTERN C</span>
</div>
<h1 class="hero-title">営業一次提案<br><span class="hero-accent">AI エージェント</span>システム</h1>
<p class="hero-sub">リサーチ → 立案 → 評価ループ → コンプライアンス → アウトプット生成 を全自動化</p>
<div class="arch-flow">
<div class="arch-node arch-blue">◈ Orchestrator</div>
<span class="arch-arrow">→</span>
<div class="arch-node arch-teal">⊞ Research ×4</div>
<span class="arch-arrow">→</span>
<div class="arch-node arch-teal">◉ Planning</div>
<span class="arch-arrow">→</span>
<div class="arch-node arch-amber">⟲ Evaluator</div>
<span class="arch-arrow">→</span>
<div class="arch-node arch-gray">⊕ Compliance</div>
<span class="arch-arrow">→</span>
<div class="arch-node arch-blue">▣ Output</div>
</div>
</div>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# INPUT FORM
# ─────────────────────────────────────────────────────────────────────────────
st.markdown('<div class="section-eyebrow">── 顧客情報入力</div>', unsafe_allow_html=True)

with st.form("input_form"):
    c1, c2, c3 = st.columns([1, 1, 1], gap="medium")
    with c1:
        client_name = st.text_input("顧客名", placeholder="例: 〇〇株式会社")
        industry    = st.selectbox("業種", ["小売EC", "アパレル", "食品・飲料", "金融", "人材", "旅行", "その他"])
    with c2:
        budget  = st.selectbox("月次広告予算規模", ["〜500万", "500〜2,000万", "2,000〜5,000万", "5,000万〜"])
        timing  = st.text_input("キャンペーン時期", placeholder="例: 2026年4〜5月 春季")
    with c3:
        kpi   = st.multiselect("主要KPI", ["CPA改善", "CV最大化", "ROAS改善", "ブランドリフト", "指名CV防衛"],
                               default=["CV最大化", "CPA改善"])
        notes = st.text_area("特記事項（任意）", height=72, placeholder="競合動向・既存課題など")

    submitted = st.form_submit_button("◈  エージェント起動", use_container_width=True, type="primary")

# ─────────────────────────────────────────────────────────────────────────────
# MOCK DATA
# ─────────────────────────────────────────────────────────────────────────────
MOCK = {
    "web": ("Web 検索サブエージェント", "teal", """**〇〇株式会社 直近ニュース（抜粋）**
- 2026/02 決算: 売上高 2,340億円（前年比 +12%）、広告宣伝費 38億円（+18%）
- 春季キャンペーン「〇〇フェア2026」を4〜5月に展開予定（プレスリリース確認）
- EC強化を中期戦略に明記、デジタル広告予算の優先配分を示唆
- 競合A社が動画広告シェアを拡大中。防衛的な指名系施策の需要が見込まれる"""),

    "rag": ("社内KB RAGサブエージェント", "teal", """**社内ナレッジ検索結果**
- 類似業種（小売EC）向け提案ナラティブ: 「検索+ショッピング一気通貫」
- 入札タイプ推奨: CV最大化 → tCPA移行ロードマップ（学習期間3〜4週）
- 禁止表現チェックリスト: 「業界最高精度」「競合比較」はNG（代替表現あり）
- 過去提案でのトップ訴求: 「計測精度向上（ITP対応）」「予算効率+23%改善」"""),

    "casedb": ("事例DBサブエージェント", "teal", """**類似案件 TOP3**

| 業種 | 施策 | 実績 |
|---|---|---|
| 小売EC | ブランド検索 × リターゲ | CPA -28%、CV +41% |
| アパレル通販 | 動画 × ショッピング | ROAS +35% |
| 家電量販 | 指名+競合指名 | 指名CVシェア +19pt |

→ 春季キャンペーン前の「ブランド守り」×「新規獲得」二軸が最も再現性高い"""),

    "market": ("市場情報サブエージェント", "teal", """**オークション環境・在庫状況**
- 小売EC キーワード CPCトレンド: +8%（前月比）、春商戦前の高騰期
- 動画在庫: 3月末〜4月上旬は残 **18%**（早期確保を推奨）
- 競合B社が先週より指名ワードへの入札を開始（アラート検知）
- 推奨: 4月1日予算スタートに向け3/20までにキャンペーン設定完了"""),

    "planning_v1": ("プランニングエージェント  ·  draft v1", "teal", """**提案骨子 v1**  /  ゴール: 春季（4〜5月）CV最大化 + 指名防衛

**推奨施策セット**
1. **検索広告 — 指名+競合指名** (月予算 ¥2,000万) — 指名CVシェア +15pt
2. **ショッピング広告** (月予算 ¥1,500万) — CV最大化入札 → 3週後にtCPA移行
3. **動画広告 (YouTube)** (月予算 ¥800万) — ブランドリフト計測付き、在庫を3/20までに確保

**パートナーシップ提案**
- ITP対応計測（コンバージョンAPI）の無償サポートを条件に予算増額を打診"""),

    "eval_1": ("エバリュエーター  ·  第1評価", "amber", """**品質評価スコア: `72 / 100`** — 改善要求 ✗

フィードバック:
- ✗ 予算配分の根拠が薄い（なぜ 2,000:1,500:800 万か）
- ✗ tCPA 移行タイミングの具体条件未記載
- ✗ 競合指名施策のコンプライアンスリスクを確認すること
- ✓ 事例との紐付けは良好
- ✓ パートナーシップ提案の方向性は適切

**→ プランニングエージェントに差し戻し（v2 要求）**"""),

    "planning_v2": ("プランニングエージェント  ·  draft v2（改訂）", "teal", """**提案骨子 v2** — 評価フィードバック反映

**予算配分根拠**
- 指名: 類似案件で最高ROI（CPA -28%実績）→ 優先配分
- ショッピング: EC強化の中期戦略と合致。CV最大化→tCPA移行は CV≥150件/月 達成後
- 動画: 在庫制約上限が ¥800万。ブランドリフト計測でブランド価値を定量化

**競合指名について**
- 入稿前に法務確認フラグを立てる（運用チームに共有）
- 代替案: 競合ワードの除外設定で自社指名防衛に絞ることも提案オプションとして提示

**tCPA移行条件**: コンバージョン数 ≥ 150件/月 かつ 学習期間3週間経過後"""),

    "eval_2": ("エバリュエーター  ·  第2評価", "amber", """**品質評価スコア: `91 / 100`** — 承認 ✓

- ✓ 予算配分に定量的根拠が追加された
- ✓ tCPA 移行条件が明確化された
- ✓ 競合指名リスクにフラグと代替案
- △ スライド構成で「顧客確認事項」スライドに懸念点をまとめること

**→ 品質閾値クリア。Compliance Agent へ転送**"""),

    "compliance": ("コンプライアンスエージェント", "gray", """**コンプライアンス・リスクチェック結果**

| チェック項目 | 結果 | 対応 |
|---|---|---|
| 社内限定情報の混入 | ✓ なし | — |
| 禁止表現 | ⚠ 1件 | 「業界最高精度」→「高精度な計測」に修正 |
| 競合指名施策 | ⚠ 要確認 | 法務レビューフラグ設定済 |
| 在庫確約表現 | ✓ 問題なし | 「残18%」は社内データのため削除 |
| スケジュールリスク | ⚠ 中 | 3/20締め切りを顧客確認事項に追記 |

**想定顧客懸念 & 打ち返し案**
- 「予算増額は決裁が必要」→ 段階的スタートプランも提示
- 「計測精度に不安」→ ITP対応の無償サポートでブロッカー解消"""),

    "output": ("アウトプットエージェント", "blue", """**生成ドキュメント一覧**

📊 **提案スライド** (Google Slides · 10枚)
> 構成: 弊社活用理由 → 活用プラン → 具体事例3件 → 発注プロセス → 顧客確認事項

💬 **セールストークスクリプト**
> オープニング / 課題提起 / 提案 / クロージング の4パート構成

📋 **顧客確認事項リスト**
> ① 春季予算上限 ② 競合指名施策の社内可否 ③ 3/20 キャンペーン設定完了可否

**営業担当向けメモ**
- 動画在庫の希少性を早期に伝え、意思決定を促す
- ITP対応は「無償サポート」として前面に出す
- tCPA移行ロードマップで「長期パートナー」ポジションを確立"""),
}

COLOR_MAP = {
    "blue":  ("◈", "blue"),
    "teal":  ("⊞", "teal"),
    "amber": ("⟲", "amber"),
    "gray":  ("⊕", "gray"),
}

# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────
def phase_header(num, label, color="blue", sublabel=""):
    sub = f'<span class="phase-sub">{sublabel}</span>' if sublabel else ""
    st.markdown(f"""
<div class="phase-row">
<div class="phase-num phase-num-{color}">{num:02d}</div>
<span class="phase-title">{label}</span>{sub}
<div class="phase-line"></div>
</div>
""", unsafe_allow_html=True)


def agent_status(key, running_label, done_label, delay, expanded_done=False):
    title, color, content = MOCK[key]
    icon, _ = COLOR_MAP[color]
    chip_html = f"""<div class="agent-chip chip-{color}"><div class="chip-dot chip-dot-{color}"></div><span class="chip-label chip-label-{color}">{title}</span></div>"""
    with st.status(f"{icon}  {running_label}", expanded=True) as status:
        st.markdown(chip_html, unsafe_allow_html=True)
        st.markdown(content)
        time.sleep(delay)
        status.update(label=done_label, state="complete", expanded=expanded_done)

# ─────────────────────────────────────────────────────────────────────────────
# EXECUTION FLOW
# ─────────────────────────────────────────────────────────────────────────────
if submitted:
    if not client_name:
        st.warning("顧客名を入力してください。")
        st.stop()
    st.session_state.agents_done  = False
    st.session_state.slides_url   = None
    st.session_state.client_info  = {
        'name': client_name, 'industry': industry,
        'budget': budget, 'timing': timing, 'kpi': kpi,
    }

if submitted:
    info = st.session_state.client_info
    st.divider()
    st.markdown(f'<div class="section-eyebrow">── 実行ログ &nbsp;/&nbsp; {info["name"]} &nbsp;·&nbsp; {info["industry"]} &nbsp;·&nbsp; {info["budget"]}</div>', unsafe_allow_html=True)

    phase_header(1, "Research", "teal", "4 サブエージェント並列実行")
    agent_status("web",    "Web 検索エージェント 実行中...",      "Web 検索  完了",       0.7)
    agent_status("rag",    "社内KB RAG エージェント 実行中...",   "社内KB RAG  完了",     0.7)
    agent_status("casedb", "事例DB エージェント 実行中...",       "事例DB  完了",         0.7)
    agent_status("market", "市場情報エージェント 実行中...",       "市場情報  完了",       0.7)

    phase_header(2, "Planning", "teal")
    agent_status("planning_v1", "プランニングエージェント 思考中...", "提案骨子 v1  生成完了", 1.5)

    phase_header(3, "Evaluator — 反省ループ", "amber", "品質閾値: 90/100")
    agent_status("eval_1",      "エバリュエーター 評価中...",         "第1評価  完了（スコア 72）",    1.2)
    agent_status("planning_v2", "プランニングエージェント 改訂中...", "提案骨子 v2  生成完了",        1.5)
    agent_status("eval_2",      "エバリュエーター 再評価中...",       "第2評価  承認（スコア 91）",   1.2)

    phase_header(4, "Compliance", "gray")
    agent_status("compliance", "コンプライアンスエージェント チェック中...", "コンプライアンスチェック  完了（3件 / 全対応済）", 1.2)

    phase_header(5, "Output", "blue")
    agent_status("output", "アウトプットエージェント 生成中...", "アウトプット生成  完了", 1.5, expanded_done=True)

    st.session_state.agents_done = True

# ── 完了セクション（エージェント完了後に常時表示）──────────────────────────
if st.session_state.agents_done:
    info = st.session_state.client_info

    st.markdown("<br>", unsafe_allow_html=True)
    st.success(f"提案資料の生成が完了しました  ·  {info['name']} / {info['industry']} / {info['budget']}")

    mc1, mc2, mc3, mc4 = st.columns(4)
    mc1.metric("総実行時間", "47 秒")
    mc2.metric("反省ループ", "2 回")
    mc3.metric("コンプライアンス指摘", "3 件")
    mc4.metric("品質スコア", "91 / 100")

    st.markdown('<div class="section-eyebrow" style="margin-top:24px;">── 次のステップ</div>', unsafe_allow_html=True)

    # ── 提案スライド ─────────────────────────────────────
    with st.expander("📊  提案スライドを生成する（Google Slides）", expanded=True):
        if st.session_state.slides_url:
            st.success("スライドの生成が完了しました")
            st.markdown(f'**[スライドを開く ↗]({st.session_state.slides_url})**')
            st.caption(st.session_state.slides_url)
        else:
            st.markdown("""
**生成されるスライド構成（6枚）**

| # | タイトル |
|---|---|
| 1 | 表紙（顧客名・提案資料） |
| 2 | SmartNews をおすすめする理由 |
| 3 | 推奨活用プラン |
| 4 | 具体的な成果事例 |
| 5 | 発注・配信スケジュール |
| 6 | 顧客確認事項 |
""")
            if st.button("◈  Google Slides を生成する", type="primary", use_container_width=True):
                with st.spinner("Google Slides を生成中... 約30〜60秒かかります"):
                    try:
                        url, _ = generate_proposal_slides(
                            info['name'], info['industry'],
                            info['budget'], info['timing'], info['kpi'],
                        )
                        st.session_state.slides_url = url
                        st.rerun()
                    except Exception as e:
                        st.error(f"生成エラー: {e}")

    # ── セールストーク ───────────────────────────────────
    with st.expander("💬  セールストークスクリプト", expanded=False):
        st.markdown(f"""
**① オープニング**
> 「本日はお時間いただきありがとうございます。{info['name']} 様の春季キャンペーンに向けて、SmartNews をどう活用いただけるか、具体的なプランをお持ちしました。」

**② 課題提起**
> 「競合A社が動画広告シェアを急拡大しており、指名ワードへの入札も確認されています。このタイミングで指名防衛と新規獲得を同時に強化することが重要です。」

**③ 提案（強調ポイント）**
> 「3施策セットをご提案します。まず検索広告で指名を守りながら、ショッピングで新規CVを最大化。動画は在庫が残り **18%** のため、3/20 までのご決断が理想的です。」
> 「ITP対応の計測精度向上サポートを無償でご提供します。CV 計測の正確性が向上し、入札最適化の精度も上がります。」

**④ クロージング**
> 「本日ご確認いただきたいのは3点です。①春季予算の上限、②競合指名施策の社内可否、③3/20までのキャンペーン設定完了の可否。いかがでしょうか？」
""")

    # ── 顧客確認事項 ─────────────────────────────────────
    with st.expander("📋  顧客確認事項リスト", expanded=False):
        st.markdown("""
- [ ] **① 春季キャンペーン予算の上限**　推奨 ¥4,300万 / 代替 ¥2,000万〜
- [ ] **② 競合指名施策の社内可否**　NG の場合は自社指名防衛プランに切り替え
- [ ] **③ 3/20 キャンペーン設定完了の可否**　動画在庫確保のため必達
- [ ] **④ ITP対応計測の導入承認**　技術担当者との日程調整が必要

| 顧客の懸念 | 打ち返し案 |
|---|---|
| 予算増額は決裁が必要 | ¥2,000万からスタートし、効果確認後に増額 |
| 計測精度に不安 | ITP対応の無償サポートでブロッカー解消 |
| 動画は未経験 | ブランドリフト計測で定量化。¥800万からの試験導入を提案 |
""")
