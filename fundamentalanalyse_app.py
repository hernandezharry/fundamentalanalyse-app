
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

            def score(val, func):
                return 0 if isinstance(val, str) else func(val)

            scores = {
                "Umsatzwachstum": score(rev_growth, lambda g: 5 if g > 10 else 3 if g > 2 else 1 if g > 0 else 0),
                "Gewinnwachstum": score(earn_growth, lambda g: 5 if g > 10 else 3 if g > 2 else 1 if g > 0 else 0),
                "Eigenkapitalrendite (ROE)": score(roe, lambda r: 5 if r > 15 else 3 if r > 10 else 1 if r > 5 else 0),
                "Verschuldung (Debt/Equity)": score(debt_to_equity, lambda d: 5 if d < 50 else 3 if d < 100 else 1),
                "KGV": score(pe_ratio, lambda p: 5 if p < 15 else 3 if p < 25 else 1),
                "PEG-Ratio": score(peg_ratio, lambda p: 5 if p < 1 else 3 if p < 2 else 1),
                "KBV": score(pb_ratio, lambda p: 5 if p < 1.5 else 3 if p < 3 else 1),
                "Dividende": 0 if isinstance(dividend_yield, str) or isinstance(payout_ratio, str)
                    else 5 if 2 <= dividend_yield <= 5 and payout_ratio < 70 else 3 if dividend_yield > 0 else 0,
                "Nettomarge": score(profit_margin, lambda m: 5 if m > 20 else 3 if m > 10 else 1),
            }

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

            total_score = sum(scores.values())

            if total_score > 40:
                interpretation = "Sehr solide Fundamentaldaten"
            elif total_score >= 30:
                interpretation = "Gut, aber genauer prüfen"
            else:
                interpretation = "Risiko höher oder Nachholbedarf"

            st.subheader("📈 Bewertungsergebnis")
            st.metric("Gesamtpunktzahl", f"{total_score}/45")
            st.info(f"💬 Interpretation: {interpretation}")

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
