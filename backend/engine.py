from collections import deque
from abc import ABC, abstractmethod

# ==========================================
# 1. THE STRATEGY PATTERN (ADVANCED OOP)
# ==========================================
class DecayStrategy(ABC):
    """Abstract base class dictating that all crops must have a decay formula."""
    @abstractmethod
    def calculate_loss(self, temperature, hours):
        pass

class TomatoDecay(DecayStrategy):
    """Specific decay algorithm for highly perishable tomatoes."""
    def calculate_loss(self, temperature, hours):
        decay_factor = 0.05 if temperature < 20 else 0.15
        return temperature * hours * decay_factor

class PotatoDecay(DecayStrategy):
    """Specific decay algorithm for hardier root vegetables."""
    def calculate_loss(self, temperature, hours):
        # Notice potatoes rot much slower than tomatoes
        decay_factor = 0.02 if temperature < 25 else 0.08
        return temperature * hours * decay_factor


# ==========================================
# 2. THE CORE BUSINESS LOGIC 
# ==========================================
class PerishableBatch:
    """Encapsulates crop data and utilizes the Strategy Pattern for degradation."""
    def __init__(self, crop_type, quantity, decay_strategy: DecayStrategy, initial_quality=100.0):
        self.crop_type = crop_type
        self.quantity = quantity
        self.decay_strategy = decay_strategy  # INJECTING THE STRATEGY
        self.quality_score = initial_quality
        self.current_value_per_kg = 40.0

    def degrade(self, temperature, hours):
        # Uses the injected strategy to calculate mathematical loss
        loss = self.decay_strategy.calculate_loss(temperature, hours)
        
        self.quality_score -= loss
        self.quality_score = max(0.0, min(100.0, self.quality_score))
        
        if self.quality_score < 30:
            self.current_value_per_kg = 0.0 
        else:
            self.current_value_per_kg *= (self.quality_score / 100.0)

    def get_total_value(self):
        return self.quantity * self.current_value_per_kg


class SupplyChainNode:
    """Base class for all physical locations utilizing a FIFO Queue."""
    def __init__(self, name, location):
        self.name = name
        self.location = location
        # DATA STRUCTURE: Using a deque for O(1) First-In-First-Out pop operations
        self.inventory = deque()

    def receive_batch(self, batch):
        self.inventory.append(batch)
        print(f"[{self.name}] Received {batch.quantity}kg of {batch.crop_type}.")

    def dispatch_oldest_batch(self):
        """FIFO Implementation: Removes and returns the oldest batch."""
        if not self.inventory:
            print(f"[{self.name}] Error: No inventory to dispatch.")
            return None
            
        # popleft() ensures we always grab the oldest item in the queue
        oldest_batch = self.inventory.popleft()
        print(f"[{self.name}] Dispatched oldest batch of {oldest_batch.crop_type}.")
        return oldest_batch


class Farm(SupplyChainNode):
    def __init__(self, name, location, daily_harvest_capacity):
        super().__init__(name, location)
        self.daily_harvest_capacity = daily_harvest_capacity

    def harvest_crop(self, crop_type, decay_strategy):
        new_batch = PerishableBatch(crop_type, self.daily_harvest_capacity, decay_strategy)
        self.inventory.append(new_batch) # Added to the right side of the queue
        print(f"[{self.name}] Harvested {self.daily_harvest_capacity}kg of fresh {crop_type}.")
        return new_batch


class Transporter(SupplyChainNode):
    def __init__(self, name, route_distance, is_refrigerated=False):
        super().__init__(name, "In-Transit")
        self.route_distance = route_distance
        self.is_refrigerated = is_refrigerated
        self.speed_kmh = 50

    def transport_batch(self, batch, ambient_temperature):
        travel_hours = self.route_distance / self.speed_kmh
        actual_temp = 4.0 if self.is_refrigerated else ambient_temperature
        
        transport_type = "Cold-Chain" if self.is_refrigerated else "Open Truck"
        print(f"[{self.name}] Transporting via {transport_type} over {self.route_distance}km...")
        
        batch.degrade(actual_temp, travel_hours)


# ==========================================
# 3. LOCAL TESTING SCRIPT
# ==========================================
if __name__ == "__main__":
    nashik_farm = Farm("Nashik Organic Farm", "Maharashtra", 1000)
    
    # 1. Harvest two different crops using the Strategy Pattern
    tomato_batch = nashik_farm.harvest_crop("Tomatoes", TomatoDecay())
    potato_batch = nashik_farm.harvest_crop("Potatoes", PotatoDecay())
    
    print("-" * 40)
    
    # 2. Dispatch the oldest batch first (FIFO Queue in action)
    # Even though we have potatoes, it MUST ship the tomatoes first.
    first_out = nashik_farm.dispatch_oldest_batch() 
    
    truck = Transporter("Standard Logistics", 170, is_refrigerated=False)
    truck.transport_batch(first_out, ambient_temperature=35.0)
    
    print(f"Final Crop Quality ({first_out.crop_type}): {first_out.quality_score:.2f}%")