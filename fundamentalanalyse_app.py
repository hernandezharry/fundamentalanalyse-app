
import streamlit as st
import yfinance as yf
import pandas as pd
from yahooquery import search

st.set_page_config(page_title="Fundamentalanalyse", layout="centered")

st.title("📊 Fundamentalanalyse von Aktien")
st.write("Gib den Namen oder Ticker der Aktie ein (z. B. Apple oder AAPL):")

user_input = st.text_input("Unternehmensname oder Ticker", "Apple")

def get_ticker_from_name(name):
    try:
        results = search(name)
        if "quotes" in results and len(results["quotes"]) > 0:
            return results["quotes"][0]["symbol"]
        return None
    except:
        return None

if user_input:
    ticker_symbol = get_ticker_from_name(user_input)
    if not ticker_symbol:
        st.error("Ticker konnte nicht gefunden werden. Bitte versuche es mit einem anderen Namen.")
    else:
        try:
            ticker = yf.Ticker(ticker_symbol)
            info = ticker.info
            hist = ticker.history(period="5y")

            # Fundamentaldaten abrufen
            roe = info.get("returnOnEquity", 0) * 100
            debt_to_equity = info.get("debtToEquity", 0)
            pe_ratio = info.get("trailingPE", 0)
            peg_ratio = info.get("pegRatio", 0)
            pb_ratio = info.get("priceToBook", 0)
            dividend_yield = info.get("dividendYield", 0) * 100
            payout_ratio = info.get("payoutRatio", 0) * 100
            profit_margin = info.get("profitMargins", 0) * 100

            # Umsatz- und Gewinnwachstum approximieren
            rev_growth = ((info.get("revenueGrowth", 0)) or 0) * 100
            earn_growth = ((info.get("earningsGrowth", 0)) or 0) * 100

            # Punkteberechnung
            def score_growth(growth):
                if growth > 10:
                    return 5
                elif growth > 2:
                    return 3
                elif growth > 0:
                    return 1
                return 0

            def score_roe(roe):
                return 5 if roe > 15 else 3 if roe > 10 else 1 if roe > 5 else 0

            def score_de(de):
                return 5 if de < 50 else 3 if de < 100 else 1

            def score_pe(pe):
                return 5 if pe < 15 else 3 if pe < 25 else 1

            def score_peg(peg):
                return 5 if peg < 1 else 3 if peg < 2 else 1

            def score_pb(pb):
                return 5 if pb < 1.5 else 3 if pb < 3 else 1

            def score_div(div, payout):
                return 5 if 2 <= div <= 5 and payout < 70 else 3 if div > 0 else 0

            def score_margin(margin):
                return 5 if margin > 20 else 3 if margin > 10 else 1

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
            score_df = pd.DataFrame(scores.items(), columns=["Kriterium", "Punkte"])
            st.dataframe(score_df.set_index("Kriterium"))

        except Exception as e:
            st.error(f"Fehler bei der Datenabfrage: {e}")
