from collections import deque
from abc import ABC, abstractmethod
import urllib.request
import json

# ==========================================
# 1. LIVE API INTEGRATION (EXTERNAL DATA)
# ==========================================
class WeatherService:
    """Fetches real-time weather data to feed the simulation."""
    @staticmethod
    def get_live_temperature(city="Nashik"):
        # Nashik Coordinates: Lat 20.0, Lon 73.78
        # Using Open-Meteo (Free, No API Key Required)
        url = "https://api.open-meteo.com/v1/forecast?latitude=20.0&longitude=73.78&current_weather=true"
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=5) as response:
                data = json.loads(response.read().decode())
                live_temp = data['current_weather']['temperature']
                print(f"[API SUCCESS] Fetched live temperature for {city}: {live_temp}°C")
                return live_temp
        except Exception as e:
            print(f"[API ERROR] Falling back to default 35.0°C. Reason: {e}")
            return 35.0

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

# ==========================================
# 4. CORE BUSINESS LOGIC (SUBJECTS & QUEUES)
# ==========================================
class PerishableBatch:
    def __init__(self, crop_type, quantity, decay_strategy: DecayStrategy, initial_quality=100.0):
        self.crop_type = crop_type
        self.quantity = quantity
        self.decay_strategy = decay_strategy
        self.quality_score = initial_quality
        self.current_value_per_kg = 40.0
        
        # Observer Pattern setup
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
        else:
            self.current_value_per_kg *= (self.quality_score / 100.0)
            
        # Broadcast state change to all observers
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
        travel_hours = int(self.route_distance / self.speed_kmh)
        actual_temp = 4.0 if self.is_refrigerated else ambient_temperature
        
        transport_type = "Cold-Chain" if self.is_refrigerated else "Open Truck"
        print(f"[{self.name}] Transporting via {transport_type} over {self.route_distance}km...")
        
        # Step through time hour-by-hour so the Observer can watch the decay live
        for hour in range(travel_hours):
            batch.degrade(actual_temp, 1)


# ==========================================
# 5. LOCAL TESTING SCRIPT
# ==========================================
if __name__ == "__main__":
    # 1. Fetch live weather data for the simulation
    live_temp = WeatherService.get_live_temperature("Nashik")
    
    nashik_farm = Farm("Nashik Organic Farm", "Maharashtra", 1000)
    
    # 2. Harvest crop and ATTACH the Quality Monitor (Observer Pattern)
    tomato_batch = nashik_farm.harvest_crop("Tomatoes", TomatoDecay())
    monitor = QualityMonitor()
    tomato_batch.attach(monitor)
    
    print("-" * 50)
    
    # 3. Dispatch and Transport using Live Weather
    first_out = nashik_farm.dispatch_oldest_batch() 
    truck = Transporter("Standard Logistics", 350, is_refrigerated=False)
    
    # Notice the alarms firing as it transports in the terminal!
    truck.transport_batch(first_out, ambient_temperature=live_temp)
    
    print("-" * 50)
    print(f"Final Crop Quality ({first_out.crop_type}): {first_out.quality_score:.2f}%")