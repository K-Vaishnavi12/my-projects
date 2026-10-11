package com.amazon.clone.inventory.event;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.math.BigDecimal;
import java.time.Instant;
import java.util.List;
import java.util.Map;

/**
 * We deserialize the order-created event as a loose Map to be resilient to
 * schema changes from the order-service. Real Amazon systems use schema registries.
 */
@Data
@NoArgsConstructor
@AllArgsConstructor
public class OrderCreatedEvent {
    private String eventId;
    private String orderId;
    private String userId;
    private Map<String, Object> order;   // raw map so different Order classes don't break us
    private Instant timestamp;

    @SuppressWarnings("unchecked")
    public List<Map<String, Object>> getItems() {
        if (order == null) return List.of();
        Object items = order.get("items");
        return items instanceof List ? (List<Map<String, Object>>) items : List.of();
    }

    public String getShippingUser() { return userId; }
}
