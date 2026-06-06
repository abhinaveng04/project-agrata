class PerishableBatch:
    """
    Encapsulation: Bundles the crop data and the methods that modify it.
    """
    def __init__(self, crop_type, quantity, initial_quality=100.0):
        self.crop_type = crop_type
        self.quantity = quantity  # in Kilograms
        self.quality_score = initial_quality  # Scale of 0 to 100
        self.current_value_per_kg = 40.0  # Base price in INR

    def degrade(self, temperature, hours):
        """Calculates food spoilage based on temperature and transit time."""
        decay_factor = 0.05 if temperature < 20 else 0.15
        loss = temperature * hours * decay_factor
        
        # Ensure quality score stays between 0 and 100
        self.quality_score -= loss
        self.quality_score = max(0.0, min(100.0, self.quality_score))
        
        # Adjust financial value dynamically
        if self.quality_score < 30:
            self.current_value_per_kg = 0.0  # Totally spoiled
        else:
            self.current_value_per_kg *= (self.quality_score / 100.0)

    def get_total_value(self):
        return self.quantity * self.current_value_per_kg


class SupplyChainNode:
    """
    Abstraction: A blueprint template for all physical locations in the chain.
    """
    def __init__(self, name, location):
        self.name = name
        self.location = location
        self.inventory = []

    def receive_batch(self, batch):
        self.inventory.append(batch)
        print(f"[{self.name}] Received {batch.quantity}kg of {batch.crop_type}.")


class Farm(SupplyChainNode):
    """
    Inheritance: Inherits from SupplyChainNode but adds harvesting logic.
    """
    def __init__(self, name, location, daily_harvest_capacity):
        super().__init__(name, location)
        self.daily_harvest_capacity = daily_harvest_capacity

    def harvest_crop(self, crop_type):
        new_batch = PerishableBatch(crop_type, self.daily_harvest_capacity)
        self.inventory.append(new_batch)
        print(f"[{self.name}] Harvested {self.daily_harvest_capacity}kg of fresh {crop_type}.")
        return new_batch


class Transporter(SupplyChainNode):
    """
    Polymorphism & Inheritance: Modifies behavior based on refrigeration status.
    """
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


# --- LOCAL TESTING SCRIPT ---
if __name__ == "__main__":
    nashik_farm = Farm("Nashik Organic Farm", "Maharashtra", 1000)
    mumbai_mandi = SupplyChainNode("Mumbai Wholesale Mandi", "Mumbai")
    
    # Run a quick test
    batch = nashik_farm.harvest_crop("Tomatoes")
    truck = Transporter("Standard Logistics", 170, is_refrigerated=False)
    
    truck.transport_batch(batch, ambient_temperature=35.0)
    mumbai_mandi.receive_batch(batch)
    
    print(f"Final Crop Quality: {batch.quality_score:.2f}%")