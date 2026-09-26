import tkinter as tk
from tkinter import ttk
import requests
import threading
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

# --- API Service ---
class CoinGeckoService:
    BASE_URL = "https://api.coingecko.com/api/v3"
    
    API_KEY = "CG-CjPyNFVrsNxZe8eh6mv9AsoU" 
    
    # Map display symbols to CoinGecko IDs
    COIN_MAP = {
        "BTC/USD": "bitcoin",
        "ETH/USD": "ethereum",
        "SOL/USD": "solana",
        "DOGE/USD": "dogecoin",
        "ADA/USD": "cardano"
    }
    
    # Add the API key to the request headers
    HEADERS = {
        "x-cg-demo-api-key": API_KEY
    }

    @classmethod
    def get_market_data(cls):
        """Fetches 24h stats for all our watchlist coins in one call."""
        ids = ",".join(cls.COIN_MAP.values())
        url = f"{cls.BASE_URL}/coins/markets"
        params = {"vs_currency": "usd", "ids": ids}
        
        try:
            # Added HEADERS to the request
            response = requests.get(url, params=params, headers=cls.HEADERS, timeout=5)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Market Data Error: {e}")
            return []

    @classmethod
    def get_chart_history(cls, coin_id):
        """Fetches 24h hourly price history for the chart."""
        url = f"{cls.BASE_URL}/coins/{coin_id}/market_chart"
        params = {"vs_currency": "usd", "days": "1"}
        
        try:
            # Added HEADERS to the request
            response = requests.get(url, params=params, headers=cls.HEADERS, timeout=5)
            response.raise_for_status()
            data = response.json()
            # Extract just the price values from the [timestamp, price] pairs
            prices = [point[1] for point in data["prices"]]
            return prices
        except Exception as e:
            print(f"Chart Data Error: {e}")
            return []

# --- GUI Classes ---
class HeaderBar(tk.Frame):
    def __init__(self, parent, refresh_callback, **kwargs):
        super().__init__(parent, bg="#1e222d", padx=10, pady=10, **kwargs)
        
        tk.Label(self, text="Select Crypto:", fg="#d1d4dc", bg="#1e222d", font=("Arial", 10)).pack(side=tk.LEFT, padx=(0, 5))
        
        # Dropdown mapped to our CoinGecko supported coins
        self.asset_combo = ttk.Combobox(self, values=list(CoinGeckoService.COIN_MAP.keys()), state="readonly")
        self.asset_combo.current(0)
        self.asset_combo.pack(side=tk.LEFT, padx=(0, 20))
        
        # We bind the combobox selection to automatically refresh
        self.asset_combo.bind("<<ComboboxSelected>>", lambda e: refresh_callback())
        
        self.refresh_btn = tk.Button(self, text="Refresh Live Data", bg="#2962ff", fg="white", relief="flat", padx=10, command=refresh_callback)
        self.refresh_btn.pack(side=tk.RIGHT)

class MetricCardsFrame(tk.Frame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, bg="#131722", pady=10, **kwargs)
        self.cards = {}
        metrics = [
            ("price", "Current Price", "Loading...", "#ffffff"),
            ("change", "24h Change", "Loading...", "#26a69a"),
            ("high", "24h High", "Loading...", "#d1d4dc"),
            ("low", "24h Low", "Loading...", "#d1d4dc"),
        ]
        
        for col, (key, title, val, color) in enumerate(metrics):
            card = tk.Frame(self, bg="#1e222d", padx=15, pady=10, relief="solid", bd=1)
            card.grid(row=0, column=col, sticky="nsew", padx=5)
            self.grid_columnconfigure(col, weight=1)

            tk.Label(card, text=title, fg="#787b86", bg="#1e222d", font=("Arial", 9)).pack(anchor="w")
            lbl_val = tk.Label(card, text=val, fg=color, bg="#1e222d", font=("Arial", 16, "bold"))
            lbl_val.pack(anchor="w", pady=(5, 0))
            self.cards[key] = lbl_val

    def update_cards(self, price, change, high, low):
        """Updates the text of the metric cards."""
        self.cards["price"].config(text=f"${price:,.2f}")
        
        color = "#26a69a" if change >= 0 else "#ef5350"
        sign = "+" if change >= 0 else ""
        self.cards["change"].config(text=f"{sign}{change:.2f}%", fg=color)
        
        self.cards["high"].config(text=f"${high:,.2f}")
        self.cards["low"].config(text=f"${low:,.2f}")

class ChartFrame(tk.Frame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, bg="#1e222d", **kwargs)
        self.fig = Figure(figsize=(6, 4), dpi=100, facecolor="#1e222d")
        self.ax = self.fig.add_subplot(111)
        self.ax.set_facecolor("#131722")
        self.ax.tick_params(colors="#787b86", labelsize=8)
        
        for spine in self.ax.spines.values():
            spine.set_color("#2a2e39")
            
        self.canvas = FigureCanvasTkAgg(self.fig, master=self)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def update_chart(self, prices, symbol):
        """Clears old chart and plots new data array."""
        self.ax.clear()
        self.ax.set_facecolor("#131722")
        self.ax.tick_params(colors="#787b86", labelsize=8)
        
        if prices:
            # Create a simple x-axis range based on the number of price points
            x_range = range(len(prices))
            self.ax.plot(x_range, prices, color="#2962ff", linewidth=2)
            self.ax.set_title(f"{symbol} 24h Trend", color="#d1d4dc", fontsize=10)
        else:
            self.ax.set_title("No Chart Data Available", color="#ef5350", fontsize=10)
            
        self.canvas.draw()

class WatchlistFrame(tk.Frame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, bg="#1e222d", **kwargs)
        tk.Label(self, text="Watchlist (Live)", fg="#d1d4dc", bg="#1e222d", font=("Arial", 11, "bold"), pady=6).pack(anchor="w", padx=10)

        columns = ("asset", "price", "change")
        self.tree = ttk.Treeview(self, columns=columns, show="headings", height=12)
        self.tree.heading("asset", text="Symbol")
        self.tree.heading("price", text="Price")
        self.tree.heading("change", text="24h %")

        self.tree.column("asset", width=70, anchor="w")
        self.tree.column("price", width=80, anchor="e")
        self.tree.column("change", width=70, anchor="e")
        self.tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    def update_watchlist(self, market_data):
        """Clears table and inserts fresh API data."""
        # Clear existing rows
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        # Match CoinGecko data back to our display symbols
        for coin in market_data:
            # Reverse lookup symbol name from ID
            symbol = next((k for k, v in CoinGeckoService.COIN_MAP.items() if v == coin["id"]), coin["symbol"].upper())
            price = f"${coin['current_price']:,.2f}"
            
            change_val = coin['price_change_percentage_24h']
            change = f"{'+' if change_val >= 0 else ''}{change_val:.2f}%"
            
            self.tree.insert("", tk.END, values=(symbol, price, change))

class StatusBar(tk.Frame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, bg="#131722", padx=10, pady=4, **kwargs)
        self.status_lbl = tk.Label(self, text="System: Ready | Waiting for API...", fg="#787b86", bg="#131722", font=("Arial", 8))
        self.status_lbl.pack(side=tk.LEFT)
        
    def update_status(self, text):
        self.status_lbl.config(text=text)

class DashboardApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Real-Time Crypto Analytics Dashboard")
        self.geometry("960x640")
        self.resizable(0,0)
        self.configure(bg="#131722")

        # Assemble layout
        self.header = HeaderBar(self, refresh_callback=self.fetch_data_thread)
        self.header.pack(fill=tk.X, side=tk.TOP)

        self.metrics = MetricCardsFrame(self)
        self.metrics.pack(fill=tk.X, side=tk.TOP, padx=10)

        self.center_frame = tk.Frame(self, bg="#131722")
        self.center_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        self.chart = ChartFrame(self.center_frame)
        self.chart.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))

        self.watchlist = WatchlistFrame(self.center_frame)
        self.watchlist.pack(side=tk.RIGHT, fill=tk.BOTH, expand=False, padx=(5, 0))

        self.status = StatusBar(self)
        self.status.pack(fill=tk.X, side=tk.BOTTOM)
        
        # Initial data fetch on startup
        self.fetch_data_thread()

    def fetch_data_thread(self):
        """Runs API calls in a background thread to prevent UI freezing."""
        self.status.update_status("System: Fetching live data from CoinGecko API...")
        self.header.refresh_btn.config(state=tk.DISABLED)
        
        # Start background thread
        threading.Thread(target=self._fetch_and_update, daemon=True).start()

    def _fetch_and_update(self):
        """Background process that hits the API and pushes data back to GUI."""
        # 1. Fetch data
        selected_symbol = self.header.asset_combo.get()
        coin_id = CoinGeckoService.COIN_MAP[selected_symbol]
        
        market_data = CoinGeckoService.get_market_data()
        chart_data = CoinGeckoService.get_chart_history(coin_id)
        
        # 2. Update UI (Must be scheduled safely back on the main thread)
        self.after(0, self._apply_ui_updates, selected_symbol, coin_id, market_data, chart_data)

    def _apply_ui_updates(self, symbol, coin_id, market_data, chart_data):
        """Applies the fetched data to the Tkinter widgets."""
        if market_data:
            self.watchlist.update_watchlist(market_data)
            
            # Find the specific data for the selected top card
            selected_coin_data = next((coin for coin in market_data if coin["id"] == coin_id), None)
            if selected_coin_data:
                self.metrics.update_cards(
                    price = selected_coin_data["current_price"],
                    change = selected_coin_data["price_change_percentage_24h"],
                    high = selected_coin_data["high_24h"],
                    low = selected_coin_data["low_24h"]
                )
        
        if chart_data:
            self.chart.update_chart(chart_data, symbol)
            
        self.status.update_status("System: Live | Data Synced Successfully")
        self.header.refresh_btn.config(state=tk.NORMAL)

if __name__ == "__main__":
    app = DashboardApp()
    app.mainloop()