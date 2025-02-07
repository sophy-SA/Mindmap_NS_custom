import streamlit as st
import google.generativeai as genai
import base64
import requests
import os
from datetime import datetime
#from dotenv import load_dotenv

###Mermaid APIによるブロック図の生成とbase64エンコード(半角記号が含まれたコードも変換可能) 
#streamlit移植版
#事前に発想を広げてからmermeidコードを出力する構成

#
#ニーズ層とシーズ層の層数など構成を定義
#発想の手順を洗練させた改良バージョン
# 既出の単語を使わないように命名規則(グループ毎の接頭辞を追加)
# + 重複のチェックや制限を無くしてその分発想の追加などが働くようにした

#シングルプロンプトの中ではほぼ完成形と思われる
#戦略指針のコメントも出るので実用価値も充分   
#  FDKのコア技術を基礎知識に埋め込んだカスタマイズバージョン
#  コア技術のリストを入れることでより具体的なキーワードになった気がする
#

# extract_mermaid_code関数の定義
def extract_mermaid_code(response_text):
    try:
        # response_textを行ごとに分割
        lines = response_text.split('\n')
        mermaid_code = []
        response_text1 = []
        response_text2 = []

        # 各行をチェック
        in_mermaid_block = False
        found_development_policy = False
        for line in lines:
            if line.strip() == '```mermaid':
                in_mermaid_block = True
                continue
            elif line.strip() == '```':
                in_mermaid_block = False
                continue

            if in_mermaid_block:
                mermaid_code.append(line)
            else:
                if "顧客価値の考察" in line:
                    found_development_policy = True

                if found_development_policy:
                    response_text2.append(line)
                else:
                    response_text1.append(line)

        # 結果を整形
        mermaid_code = '\n'.join(mermaid_code)
        response_text1 = '\n'.join(response_text1)
        response_text2 = '\n'.join(response_text2)

        return response_text1, response_text2, mermaid_code
    except Exception as e:
        st.error(f"エラーが発生しました: {str(e)}")

# Gemini APIの設定
genai.configure(api_key='AIzaSyA35e8FnZfrxjTP7_RBZQvAm7sjGwb6TWI')
#model = genai.GenerativeModel('gemini-1.5-pro')
model = genai.GenerativeModel('gemini-2.0-flash-exp')
#model = genai.GenerativeModel('gemini-2.0-flash-thinking-exp')

# 環境変数の読み込み版
#load_dotenv()
#genai.configure(api_key=os.getenv('GOOGLE_API_KEY'))
#model = genai.GenerativeModel('gemini-pro')

# Streamlitのページ設定
st.set_page_config(page_title="マインドマップジェネレーター", layout="wide")
st.title("ニーズとシーズの深堀りマップ")

# セッション状態の初期化
if 'img_data' not in st.session_state:
    st.session_state.img_data = None
if 'img_url' not in st.session_state:
    st.session_state.img_url = None
if 'mermaid_code' not in st.session_state:
    st.session_state.mermaid_code = None
if 'response_text1' not in st.session_state:
    st.session_state.response_text1 = None
if 'response_text2' not in st.session_state:
    st.session_state.response_text2 = None


# 入力フォームの作成
prompt1 = st.text_input("ターゲットにする製品/用途/購買層を入力：　例) □□向け、○○を△△する、○○用品など")
prompt2 = st.text_input("保有する技術/製品/サービスを入力：　例）○○製造技術、△△マネジメントサービスなど")
prompt3 = st.text_area("指示内容、注意点、参考情報：", value="特になし")

# 推論開始ボタンが押されたときの処理
if st.button("推論開始(マップを生成)"):
    if prompt1 and prompt2:
        try:
            # プロンプトの作成
            prompt = f"""
            ##指示
            あなたは優秀なプロダクト開発支援のプロコンサルタントです。
            ターゲットのニーズに向けて保有技術の進化や発展の方向を考察するマインドマップを作成します。
            作成したマインドマップをMermaidで描画するためのコードとそれを作成するための発想の履歴を回答してください。

            
            ##マインドマップの形式
            左の端にユーザーの設定したニーズがあり、ニーズから用途や利用シーンを発想していく。
            発想した要素からさらに発想をつなげて独創的で多様なたくさんの要素を発想する。
            発想は右に向かって広がり、キーワードが増える。

            反対側(右端)にユーザーの設定したシーズ(保有している技術、製品、サービス)がある。
            シーズから左に向かって、応用や転換、または組み合わせで作れる技術を発想して増やしていく。

            中央には要求される特性がある。
            発想で広がったニーズから求められる特性と応用で広がったシーズ技術、製品、サービスが提供できる特性が
            中央の要求特性にある多数のキーワードを介してつながる構成。
            部分的に接続しないキーワードがあってもよい。接続できなくても重要と思われるキーワードは残す。

            ##ニーズ/ターゲットにする製品、ユーザー層、用途：{prompt1}
            ##シーズ/保有している技術、製品、サービス：：{prompt2}

            ##キーワード名のルール
            ・各キーワードは、どのグループに属した単語であるか分かりやすい語句を選択する
            ・ニーズの発想グループは利用シーンや用途、特徴を表す単語を使う。(例：○○しない、△△できる、□□用途 など)。
            ・「ニーズの第1層」の単語は前に"i"、「ニーズの第2層」の単語は前に"l"、をつける
            ・シーズの応用グループは技術やサービス、性能、機能を表す単語を使う。(例：△△技術、□□サービス、○○の向上、▼▼の活用 など)。
            ・「シーズの第1層」の単語は前に"o"、「シーズの第2層」の単語は前に"r"、をつける
            ・要求特性のグループは特性や性質を表す単語を使う。(例：高耐久、軽量、○○性、□□化 など)。
            ・キーワードの名前には( 、 ) 、 [ 、]、【、】、/、・、~などの記号や特殊な文字は使わない。これらを使う時は「_」に置き換える。

            #留意点、指針、参考知識：：{prompt3}

            #自社のコア技術一覧(シーズの応用や強みの考察に利用する)
            3Dモデリング設計
            高密度配線基板設計
            ハーネス設計
            磁性材料設計
            ノイズ抑制技術
            双方向性　制御技術
            ノイズ低減化技術
            インターリーブ技術
            ピークシフト制御技術
            出力電力のバランス化技術
            ソフトスイッチング技術
            同期整流技術
            充放電制御技術
            セルバランス技術
            非接触給電
            Androidアプリ設計
            iOSアプリ設計
            Linuxアプリ設計
            Webアプリ設計
            Windowsアプリ設計
            高密度実装技術
            EMC・ESD設計
            水冷冷却方式設計
            放熱設計
            温度計測技術
            電圧計測技術
            電池内部抵抗測定技術
            電流計測技術
            アンテナ設計
            高周波回路設計
            高周波電磁界シミュレーション技術
            無線通信回路設計
            無線通信性能評価技術
            測定機器 制御ソフト設計
            測定機器 制御ソフト設計
            メカ(マシン）制御ソフト設計
            ポッテイング加工技術
            金属基板実装
            多層基板実装
            レーザトリミング加工技術
            ACF接続技術
            COB技術
            TAB技術
            Wボンディング技術
            厚膜印刷技術
            アンダーフィル技術
            射出成型技術
            樹脂モールドPKG技術
            積層印刷技術
            ダイシング加工技術
            はんだ転写実装技術
            フラックス転写実装技術
            ブリスタパック加工
            防水加工技術
            溶接加工技術
            データベース設計
            デジタルF/B制御技術
            A/D　変換回路設計
            ASIC/FPGA　回路設計
            D/A　変換回路設計
            FPGA 回路設計
            通信制御設計
            圧電センサ
            温度センサ
            角速度センサ
            加速度センサ
            気圧センサ
            湿度センサ
            照度センサ
            AC/DC変換回路設計
            DC/DC変換回路設計
            PFC制御回路設計
            交流インバータ回路設計
            充電回路設計
            トランス・コイル部品設計
            放電回路設計
            ニッケル水素電池設計
            電池マネージメント技術/シュミレーション
            アルカリ電池設計
            リチウム電池設計（円筒スパイラル）
            リチウム電池設計（円筒ボビン）
            リチウム電池設計（薄形ラミネート）
            リチウム電池設計（コイン）
            材料シュミレーション技術(第一原理)
            XRD構造解析
            ミクロ構造解析技術
            AI材料開発技術
            新電池設計（量産以外）
            生産設備設計
            全固体電池設計
            電池封口技術
            電池封口技術（レーザー封口）
            電池封口シュミレーション技術
            熱流体シミュレーション技術
            電池パック/モジュール設計
            粉体表面制御技術
            電極製造技術（混合、塗布）
            電極製造技術（造粒）
            電極製造技術（成型）
            電極製造技術（シート化）
            金属リチウム取り扱い
            非水電解液
            ドライバ設計
            ファーム設計
            MISRA-C
            コード レビュー・デバッグ
            プロジェクトマネジメント
            満充電検知
            分割充電技術
            すり足充電技術
            多段階充電技術
            充電残時間予測技術
            多段階放電技術
            短時間停電検知技術
            アシスト放電技術
            寿命残月数予測技術
            データ解析(AI・機械学習)

            #手順1、ニーズの発想
            設定されたニーズから利用シーンや用途、特徴を発想して様々なキーワードを提案して出力する(ニーズの第1層)。
            「ニーズの第1層」のキーワードからさらに新たな利用シーンや用途を発想して出力する(ニーズの第2層)。
            「ニーズの第2層」のキーワードから「ニーズの要求特性」の候補をたくさん発想して出力する。
            発想は柔軟で独創的なものを重視する。

            #手順2、シーズの応用
            設定されたシーズを応用して開発できる技術、または提供できるサービスや機能を提案して出力する(シーズの第1層)。
            「シーズの第1層」をさらに応用、または組み合わせて開発できる技術、製品、サービスを提案して出力する(シーズの第2層)。
            「シーズの第1層」を基に「シーズの第2層」はより多くの技術や製品を産み出す。
            「シーズの第2層」が提供できる「シーズ要求特性」の候補をたくさん発想して出力する。
            「シーズの要求特性」で出力する単語は、「ニーズの要求特性」の単語と意味が近いものがある場合は同じ言葉にする。
            シーズの応用は単純な転換ではなく、柔軟で独創的なものを重視する。
            強みとして「自社のコア技術一覧」の項目を優先する。「自社のコア技術一覧」の応用や組み合わせで得られる項目も優先する。

            #手順3、ニーズとシーズに共通する「要求特性」の抽出
            ニーズの発想とシーズの応用の出力結果から、どのような「要求特性」が両者に共通するか考察して出力する。
            共通する「要求特性」をマインドマップに記載する項目として抽出する。
            競争力を高めるため、独自性のあるものや差別化が行える項目を重要視してとりあげる。
            重要な項目は共通していなくても抽出して出力する。

            #手順4、「要求特性」からの発想の追加
            共通しておらず接続できない「ニーズの要求特性」について、可能なら、これと繋げられるシーズ応用の発想を追加する。
            「シーズの第2層」⇒「シーズの第1層」の順に逆に発想して出力する。
            共通しておらず接続できない「シーズの要求特性」について、可能なら、これと繋げられるニーズの発想を追加する。
            「ニーズの第2層」⇒「ニーズの第1層」の順に逆に発想して出力する。

            ここまでの回答結果を基に、マインドマップで描画する各層のキーワードを決定し出力する。

            #手順5、マインドマップ構成の決定とMermaidのオブジェクト図の作成
            ここまで出力した内容を基に「マインドマップの形式」に沿ってマインドマップの構成を決定する。。
            顧客価値の創出について下記の解説と提案を行ってして出力する。

            ・「顧客価値の考察」と出力する
            ・シーズ技術が顧客に提供できる本質的な価値や強味と有望なターゲット
            ・市場ニーズからみたターゲット層が求めている価値と有効な技術やサービス
            ・ニーズにマッチし、且つ自社のコア技術を活かせる開発方針やテーマ
            ・開発において競争力を向上させ、他社に模倣されないための留意点

            決定したマインドマップを描画するMermaidのオブジェクト図を作成するコードを出力する。

            Mermaidのコード部分は「```mermaid」と「```」で囲むことで明示します。
            オブジェクト図は左から右に並べる構成にするので、最初に必ず「flowchart LR」を記述する。
            設定したニーズを左端として、「ニーズ」、「ニーズの第1層」、「ニーズの第2層」、「要求特性」の順にそれぞれのキーワードを接続する。
            「要求特性」から「シーズの第2層」「シーズの第1層」の順にそれぞれ接続されて「設定したシーズ」に接続し収束する。
            ＊重要：Mermaidの接続関係は「<==」を使えない。シーズグループの接続関係は必ず「<==>」を使うこと。


            ##mermaidコード部分の出力例(ニーズ：「日常で気軽に持ち運べる」、シーズ：「ニッケル水素電池」の場合)##
            ```mermaid
            flowchart LR
            %% テーマ設定
            classDef default fill:#f0f0f0,stroke:#555,stroke-width:4px,font-weight: bold,font-size: 20px;

            %% ニーズ側
            subgraph "ニーズの展開"
            %% 設定したニーズ==>ニーズの第1層
                日常生活で気軽に持ち運べる ==> i外出先で使う
                日常生活で気軽に持ち運べる ==> iいつでも使える
                日常生活で気軽に持ち運べる ==> iトラブル対応
            %% ニーズの第1層==>lニーズの第2層
                i外出先で使う ==> lモバイル機器用電源
                i外出先で使う ==> lポータブル家電用電源
                iいつでも使える ==> l超省電力
                iいつでも使える ==> l繰り返し長く使える
                iトラブル対応 ==> l非常用電源


            end
            %% ニーズの第2層==>要求特性
                lモバイル機器用電源 ==> 軽量性
                lモバイル機器用電源 ==> 高出力
                lポータブル家電用電源 ==> 長寿命
                lポータブル家電用電源 ==> 安全性
                lポータブル家電用電源 ==> 多様な出力電圧
                l超省電力 ==> 急速充電
                l超省電力 ==> 信頼性
                l繰り返し長く使える ==> 信頼性
                l繰り返し長く使える ==> 耐衝撃性
                l非常用電源 ==> 耐衝撃性
                l非常用電源 ==> 携帯性

            %% 求められる特性
            subgraph "要求特性"
                軽量性
                高出力
                長寿命
                安全性
                多様な出力電圧
                急速充電
                信頼性
                耐衝撃性
                携帯性
            end

            %% 要求特性==>シーズの第2層
            軽量性 ==> r高エネルギー密度
            軽量性 ==> r小型パッケージ技術
            高出力 ==> r高電流放電特性
            長寿命 ==> rサイクル寿命向上
            安全性 ==> r過充電防止機能
            安全性 ==> r短絡防止機能
            多様な出力電圧 ==> rDCコンバータ技術
            急速充電 ==> r高速充電技術
            信頼性 ==> r安定した出力
            信頼性 ==> r自己診断機能
            耐衝撃性 ==> r堅牢な構造設計
            携帯性 ==> r軽量コンパクト設計

            %% シーズ側
            subgraph "保有技術"
            %% シーズの第2層<==>シーズの第1層
                r高エネルギー密度 <==> o高密度化技術
                r小型パッケージ技術 <==> o高密度化技術
                r高電流放電特性 <==> o電極材料改良
                rサイクル寿命向上 <==> o電解液改良
                r過充電防止機能 <==> o回路設計技術
                r短絡防止機能 <==> o回路設計技術
                rDCコンバータ技術 <==> o回路設計技術
                r高速充電技術 <==> o充電制御技術
                r安定した出力 <==> o電池管理システム
                r自己診断機能 <==> o電池管理システム
                r堅牢な構造設計 <==> o筐体設計技術
                r軽量コンパクト設計 <==> o筐体設計技術

            %% シーズの第1層==>設定したシーズ技術
                o高密度化技術 <==> ニッケル水素電池
                o電極材料改良 <==> ニッケル水素電池
                o電解液改良 <==> ニッケル水素電池
                o回路設計技術 <==> ニッケル水素電池
                o充電制御技術 <==> ニッケル水素電池
                o電池管理システム <==> ニッケル水素電池
                o筐体設計技術 <==> ニッケル水素電池
            end

            classDef needs fill:#e0f7fa,stroke:transparent,stroke-width:2px,font-weight: bold,font-size: 30px;
            class ニーズの展開 needs

            classDef property fill:transparent,stroke:transparent,stroke-width:2px,font-weight: bold,font-size: 30px;
            class 要求特性 property

            classDef seeds fill:#ffcccc,stroke:transparent,stroke-width:2px,font-weight: bold,font-size: 30px;
            class 保有技術 seeds
            ```

            """

            # Geminiでマインドマップのコードを生成
            response = model.generate_content(prompt)

            ## responseの結果を表示 エラー発生時のデバッグ用
            #st.write("### Geminiからの応答:")
            #st.write(response.text)

            # AIの応答を解説とMermaidコードに分割
            response_text1, response_text2, mermaid_code = extract_mermaid_code(response.text)


            # Mermaid形式のコードを抽出して整形
            #mermaid_code = response.text.strip()
            #if not mermaid_code.startswith('flowchart'):
            #    mermaid_code = 'flowchart LR\n' + mermaid_code
            
            # Mermaid APIのエンドポイント
            mermaid_api_url = "https://mermaid.ink/img/"
            
            # mermaidコードをbase64エンコード
            mermaid_code_bytes = mermaid_code.encode('utf-8')
            base64_code = base64.urlsafe_b64encode(mermaid_code_bytes).decode('utf-8')
            
            # 画像URLの生成
            img_url = f"{mermaid_api_url}{base64_code}"
            
            # 画像の取得と表示
            response = requests.get(img_url)
            if response.status_code == 200:
                # セッション状態に画像データとURLを保存
                st.session_state.img_data = response.content
                st.session_state.img_url = img_url
                st.session_state.mermaid_code = mermaid_code
                st.session_state.response_text1 = response_text1
                st.session_state.response_text2 = response_text2

            else:
                st.session_state.img_data = []
                st.session_state.img_url = []
                st.session_state.mermaid_code = mermaid_code
                st.session_state.response_text1 = response_text1
                st.session_state.response_text2 = response_text2
                st.error(f"画像の生成に失敗しました。コードとAIの回答を確認してください。ステータス: {response.status_code}")
        
        except Exception as e:
            st.error(f"エラーが発生しました: {str(e)}")
    else:
        st.warning("未入力の項目があります")

               
# 現在の日時を使用してユニークなファイル名を生成
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

# 画像の取得と表示
if st.session_state.img_data:
    # 生成されたマインドマップの表示
    st.image(st.session_state.img_url, caption="生成されたマップ", use_container_width=True)
 
    # 画像ダウンロードボタン
    st.download_button(
        label="マップをダウンロード",
        data=st.session_state.img_data,
        file_name=f"needs_map_{timestamp}.png",
        mime="image/png"
    )

# AIの解説部分の表示とダウンロード
if 'response_text2' in st.session_state and st.session_state.response_text2:
    st.write(st.session_state.response_text2)

    st.download_button(
        label="分析結果のダウンロード",
        data=st.session_state.response_text2,
        file_name=f"ai_explanation_part2_{timestamp}.txt",
        mime="text/plain"
    )


if 'response_text1' in st.session_state and st.session_state.response_text1:
    with st.expander("ニーズ/シーズの種だし部分を表示"):
        st.text(st.session_state.response_text1)

    st.download_button(
        label="種だし部分のダウンロード",
        data=st.session_state.response_text1,
        file_name=f"ai_explanation_part1_{timestamp}.txt",
        mime="text/plain"
    )

                
if st.session_state.mermaid_code:
    # Mermaidコードの表示（オプション）
    with st.expander("描画コードを表示(Mermaid)"):
        st.code(st.session_state.mermaid_code, language="mermaid")

    # Mermaidコードダウンロードボタン
    st.download_button(
        label="描画コード ダウンロード",
        data=st.session_state.mermaid_code,
        file_name=f"needs_map_{timestamp}.txt",
        mime="text/plain"
    )


