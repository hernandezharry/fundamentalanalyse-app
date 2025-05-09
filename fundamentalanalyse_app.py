
import streamlit as st
import yfinance as yf
import pandas as pd
from yahooquery import search
import math

st.set_page_config(page_title="Fundamentalanalyse", layout="centered")

st.title("📊 Fundamentalanalyse von Aktien")
st.write("Gib den Namen oder Ticker der Aktie ein (z. B. Apple oder AAPL):")

user_input = st.text_input("Unternehmensname oder Ticker", "Apple")

def get_valid_ticker(user_input):
    ticker = yf.Ticker(user_input)
    try:
        info = ticker.info
        if info and info != {}:
            return user_input, info
    except:
        pass

    try:
        results = search(user_input)
        if "quotes" in results and len(results["quotes"]):
            symbol = results["quotes"][0]["symbol"]
            ticker = yf.Ticker(symbol)
            try:
                info = ticker.info
                if info and info != {}:
                    return symbol, info
            except:
                return None, None
    except Exception as e:
        st.error(f"Fehler bei der Namenssuche: {e}")
    return None, None

def fmt(value):
    if value is None or (isinstance(value, float) and (math.isnan(value) or abs(value) > 1e8)):
        return "n.v."
    return round(value, 2)

if user_input:
    ticker_symbol, info = get_valid_ticker(user_input)
    if not ticker_symbol or not info:
        st.error("Ticker konnte nicht gefunden werden. Bitte versuche es mit einem anderen Namen.")
    else:
        try:
            ticker = yf.Ticker(ticker_symbol)
            hist = ticker.history(period="5y")

            # Rohwerte abrufen
            roe = fmt(info.get("returnOnEquity", 0) * 100)
            debt_to_equity = fmt(info.get("debtToEquity", 0))
            pe_ratio = fmt(info.get("trailingPE", 0))
            peg_ratio = fmt(info.get("pegRatio", 0))
            pb_ratio = fmt(info.get("priceToBook", 0))
            dividend_yield = fmt(info.get("dividendYield", 0) * 100)
            payout_ratio = fmt(info.get("payoutRatio", 0) * 100)
            profit_margin = fmt(info.get("profitMargins", 0) * 100)
            rev_growth = fmt((info.get("revenueGrowth", 0)) or 0 * 100)
            earn_growth = fmt((info.get("earningsGrowth", 0)) or 0 * 100)

            def score_growth(growth):
                if isinstance(growth, str): return 0
                if growth > 10: return 5
                elif growth > 2: return 3
                elif growth > 0: return 1
                return 0

            def score_roe(roe):
                if isinstance(roe, str): return 0
                return 5 if roe > 15 else 3 if roe > 10 else 1 if roe > 5 else 0

            def score_de(de):
                if isinstance(de, str): return 0
                return 5 if de < 50 else 3 if de < 100 else 1

            def score_pe(pe):
                if isinstance(pe, str): return 0
                return 5 if pe < 15 else 3 if pe < 25 else 1

            def score_peg(peg):
                if isinstance(peg, str): return 0
                return 5 if peg < 1 else 3 if peg < 2 else 1

            def score_pb(pb):
                if isinstance(pb, str): return 0
                return 5 if pb < 1.5 else 3 if pb < 3 else 1

            def score_div(div, payout):
                if isinstance(div, str) or isinstance(payout, str): return 0
                return 5 if 2 <= div <= 5 and payout < 70 else 3 if div > 0 else 0

            def score_margin(margin):
                if isinstance(margin, str): return 0
                return 5 if margin > 20 else 3 if margin > 10 else 1

            metrics = {
                "Umsatzwachstum": rev_growth,
                "Gewinnwachstum": earn_growth,
                "Eigenkapitalrendite (ROE)": roe,
                "Verschuldung (Debt/Equity)": debt_to_equity,
                "KGV": pe_ratio,
                "PEG-Ratio": peg_ratio,
                "KBV": pb_ratio,
                "Dividende": dividend_yield,
                "Nettomarge": profit_margin,
            }

            scores = {
                "Umsatzwachstum": score_growth(rev_growth),
                "Gewinnwachstum": score_growth(earn_growth),
                "Eigenkapitalrendite (ROE)": score_roe(roe),
                "Verschuldung (Debt/Equity)": score_de(debt_to_equity),
                "KGV": score_pe(pe_ratio),
                "PEG-Ratio": score_peg(peg_ratio),
                "KBV": score_pb(pb_ratio),
                "Dividende": score_div(dividend_yield, payout_ratio),
                "Nettomarge": score_margin(profit_margin),
            }

            total_score = sum(scores.values())

            st.subheader("📈 Bewertungsergebnis")
            st.metric("Gesamtpunktzahl", f"{total_score}/45")

            st.write("### Einzelbewertungen:")
            score_df = pd.DataFrame({
                "Kriterium": list(scores.keys()),
                "Wert": list(metrics.values()),
                "Punkte": list(scores.values())
            })
            st.dataframe(score_df.set_index("Kriterium"))

            csv = score_df.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Download als CSV", data=csv, file_name=f"fundamentalanalyse_{ticker_symbol}.csv", mime='text/csv')

        except Exception as e:
            st.error(f"Fehler bei der Datenverarbeitung: {e}")
