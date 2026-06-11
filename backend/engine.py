from collections import deque
from abc import ABC, abstractmethod
import urllib.request
import json
import os
import math

# ==========================================
# 1. LIVE API INTEGRATION (EXTERNAL DATA)
# ==========================================
class WeatherService:
    """Fetches real-time weather data to feed the simulation."""
    @staticmethod
    def get_live_temperature(city, lat, lon):
        # Dynamically inject the coordinates into the API URL
        url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true"
        try:
            assert url.startswith("https://"), "Only HTTPS allowed"
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=5) as response:
                data = json.loads(response.read().decode())
                live_temp = data['current_weather']['temperature']
                print(f"[API SUCCESS] Fetched live temp for {city}: {live_temp}°C")
                return live_temp
        except Exception as e:
            print(f"[API ERROR] Falling back to default 35.0°C. Reason: {e}")
            return 35.0

class MandiService:
    @staticmethod
    def get_live_mandi_price(crop_type):
        # FIX: Safely remove plurals without mutilating base words
        if crop_type.endswith("oes"):
            crop_query = crop_type[:-2]  # Tomatoes -> Tomato
        elif crop_type.endswith("s") and not crop_type.endswith("ss"):
            crop_query = crop_type[:-1]  # Apples -> Apple
        else:
            crop_query = crop_type       # Spinach -> Spinach
        
        # FIX: Use environment variable for API key
        API_KEY = os.environ.get("DATA_GOV_IN_KEY", "")
        url = (
            f"https://api.data.gov.in/resource/9ef84268-d588-465a-a308-a864a43d0070"
            f"?api-key={API_KEY}&format=json"
            f"&filters[commodity]={crop_query}"
        )
        
        # Enterprise-grade wholesale price index fallbacks (₹/kg) if government gateway rate-limits are active
        market_defaults = {
            "Tomatoes": 32.0, "Potatoes": 22.0, "Mangoes": 85.0, "Spinach": 25.0,
            "Capsicum": 50.0, "Litchi": 120.0, "Orange": 60.0, "Rice": 44.0,
            "Wheat": 28.0, "Banana": 35.0, "Apple": 115.0, "Onion": 26.0
        }
        
        try:
            assert url.startswith("https://"), "Only HTTPS allowed"
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=3) as response:
                data = json.loads(response.read().decode())
                if "records" in data and len(data["records"]) > 0:
                    # Government indexes represent prices per Quintal (100 kg). Convert to Kilograms.
                    modal_price_quintal = float(data["records"][0]["modal_price"])
                    live_price_kg = modal_price_quintal / 100.0
                    if live_price_kg > 0:
                        print(f"[MANDI API SUCCESS] Live wholesale rate for {crop_type}: ₹{live_price_kg}/kg")
                        return live_price_kg
        except Exception as e:
            print(f"[MANDI FALLBACK] Gateway latency. Utilizing local baseline index. Info: {e}")
            
        return market_defaults.get(crop_type, 40.0)

# ==========================================
# 2. THE OBSERVER PATTERN (EVENT-DRIVEN ARCHITECTURE)
# ==========================================
class Observer(ABC):
    @abstractmethod
    def update(self, batch):
        pass

class QualityMonitor(Observer):
    """Watches inventory and fires alerts if quality drops below critical levels."""
    def update(self, batch):
        if batch.quality_score < 60.0 and batch.quality_score > 0.0:
            print(f"  [CRITICAL ALERT] 🚨 {batch.crop_type} quality dropped to {batch.quality_score:.1f}%!")
        elif batch.quality_score == 0.0:
            print(f"  [FATAL ALERT] 💀 {batch.crop_type} has completely spoiled. Write-off required.")

# ==========================================
# 3. THE STRATEGY PATTERN (DECAY ALGORITHMS)
# ==========================================
class DecayStrategy(ABC):
    @abstractmethod
    def calculate_loss(self, temperature, hours):
        pass

class TomatoDecay(DecayStrategy):
    def calculate_loss(self, temperature, hours):
        decay_factor = 0.05 if temperature < 20 else 0.15
        return temperature * hours * decay_factor

class PotatoDecay(DecayStrategy):
    def calculate_loss(self, temperature, hours):
        decay_factor = 0.02 if temperature < 25 else 0.08
        return temperature * hours * decay_factor
        
class MangoDecay(DecayStrategy):
    """Specific decay algorithm for tropical fruits."""
    def calculate_loss(self, temperature, hours):
        decay_factor = 0.03 if temperature < 20 else 0.12
        return temperature * hours * decay_factor

class SpinachDecay(DecayStrategy):
    """Specific decay algorithm for highly perishable leafy greens."""
    def calculate_loss(self, temperature, hours):
        # Spinach wilts incredibly fast in heat
        decay_factor = 0.08 if temperature < 15 else 0.25
        return temperature * hours * decay_factor

class GrainDecay(DecayStrategy):
    """Base decay for dry grains."""
    def calculate_loss(self, temperature, hours):
        decay_factor = 0.01 if temperature < 25 else 0.05
        return temperature * hours * decay_factor

class RiceDecay(GrainDecay): pass

class WheatDecay(GrainDecay): pass

class BananaDecay(DecayStrategy):
    """Specific decay algorithm for Banana."""
    def calculate_loss(self, temperature, hours):
        decay_factor = 0.07 if temperature < 22 else 0.15
        return temperature * hours * decay_factor

class AppleDecay(DecayStrategy):
    """Specific decay algorithm for Apple."""
    def calculate_loss(self, temperature, hours):
        decay_factor = 0.01 if temperature < 18 else 0.05
        return temperature * hours * decay_factor

class OnionDecay(DecayStrategy):
    """Specific decay algorithm for Onion."""
    def calculate_loss(self, temperature, hours):
        decay_factor = 0.01 if temperature < 25 else 0.04
        return temperature * hours * decay_factor
        
class CapsicumDecay(DecayStrategy):
    """Specific decay algorithm for Capsicum."""
    def calculate_loss(self, temperature, hours):
        decay_factor = 0.04 if temperature < 18 else 0.12
        return temperature * hours * decay_factor

class LitchiDecay(DecayStrategy):
    """Specific decay algorithm for Litchi."""
    def calculate_loss(self, temperature, hours):
        decay_factor = 0.06 if temperature < 15 else 0.20
        return temperature * hours * decay_factor
        
class OrangeDecay(DecayStrategy):
    """Specific decay algorithm for Orange."""
    def calculate_loss(self, temperature, hours):
        decay_factor = 0.02 if temperature < 20 else 0.06
        return temperature * hours * decay_factor


# ==========================================
# 4. CORE BUSINESS LOGIC (SUBJECTS & QUEUES)
# ==========================================
BASE_VALUE_PER_KG = 40.0
class PerishableBatch:
    def __init__(self, crop_type, quantity, decay_strategy: DecayStrategy, initial_quality=100.0):
        self.crop_type = crop_type
        self.quantity = quantity
        self.decay_strategy = decay_strategy
        self.quality_score = initial_quality
        self.base_value_per_kg = BASE_VALUE_PER_KG # Store the baseline mathematically
        self.current_value_per_kg = self.base_value_per_kg
        self._observers = []

    def attach(self, observer: Observer):
        self._observers.append(observer)

    def notify(self):
        for observer in self._observers:
            observer.update(self)

    def degrade(self, temperature, hours):
        loss = self.decay_strategy.calculate_loss(temperature, hours)
        self.quality_score -= loss
        self.quality_score = max(0.0, min(100.0, self.quality_score))
        
        if self.quality_score < 30:
            self.current_value_per_kg = 0.0
        elif self.quality_score < 70:
            # Gradual discount for mid-tier quality
            discount = (self.quality_score - 30) / 40
            self.current_value_per_kg = self.base_value_per_kg * discount * 0.6
        else:
            self.current_value_per_kg = self.base_value_per_kg * (self.quality_score / 100.0)
            
        self.notify()

    def get_total_value(self):
        return self.quantity * self.current_value_per_kg


class SupplyChainNode:
    def __init__(self, name, location):
        self.name = name
        self.location = location
        self.inventory = deque() # FIFO Queue

    def receive_batch(self, batch):
        self.inventory.append(batch)
        print(f"[{self.name}] Received {batch.quantity}kg of {batch.crop_type}.")

    def dispatch_oldest_batch(self):
        if not self.inventory:
            return None
        oldest_batch = self.inventory.popleft()
        print(f"[{self.name}] Dispatched oldest batch of {oldest_batch.crop_type}.")
        return oldest_batch


class Farm(SupplyChainNode):
    def __init__(self, name, location, daily_harvest_capacity):
        super().__init__(name, location)
        self.daily_harvest_capacity = daily_harvest_capacity

    def harvest_crop(self, crop_type, decay_strategy):
        new_batch = PerishableBatch(crop_type, self.daily_harvest_capacity, decay_strategy)
        self.inventory.append(new_batch)
        print(f"[{self.name}] Harvested {self.daily_harvest_capacity}kg of fresh {crop_type}.")
        return new_batch


class Transporter(SupplyChainNode):
    def __init__(self, name, route_distance, is_refrigerated=False):
        super().__init__(name, "In-Transit")
        self.route_distance = route_distance
        self.is_refrigerated = is_refrigerated
        self.speed_kmh = 50

    def transport_batch(self, batch, ambient_temperature):
        # FIX: Use math.ceil to round up and capture all transit time
        travel_hours = math.ceil(self.route_distance / self.speed_kmh)
        actual_temp = 4.0 if self.is_refrigerated else ambient_temperature
        
        transport_type = "Cold-Chain" if self.is_refrigerated else "Open Truck"
        print(f"[{self.name}] Transporting via {transport_type} over {self.route_distance}km...")
        
        # Step through time hour-by-hour so the Observer can watch the decay live
        for hour in range(travel_hours):
            batch.degrade(actual_temp, 1)
            if batch.quality_score <= 0.0:
                break

# ==========================================
# 5. LOCAL TESTING SCRIPT
# ==========================================
if __name__ == "__main__":
    # 1. Fetch live weather data (passing the coordinates!)
    live_temp = WeatherService.get_live_temperature("Nashik", 20.0, 73.78)
    
    nashik_farm = Farm("Nashik Organic Farm", "Maharashtra", 1000)
    tomato_batch = nashik_farm.harvest_crop("Tomatoes", TomatoDecay())
    monitor = QualityMonitor()
    tomato_batch.attach(monitor)
    
    print("-" * 50)
    first_out = nashik_farm.dispatch_oldest_batch() 
    truck = Transporter("Standard Logistics", 350, is_refrigerated=False)
    truck.transport_batch(first_out, ambient_temperature=live_temp)
    
    print("-" * 50)
    print(f"Final Crop Quality ({first_out.crop_type}): {first_out.quality_score:.2f}%")