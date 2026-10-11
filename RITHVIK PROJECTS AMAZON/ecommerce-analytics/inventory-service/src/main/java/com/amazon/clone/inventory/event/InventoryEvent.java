package com.amazon.clone.inventory.event;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.io.Serializable;
import java.time.Instant;
import java.util.List;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class InventoryEvent implements Serializable {
    private String eventId;
    private String orderId;
    private String userId;
    private String status;                 // RESERVED | FAILED
    private String reason;                 // when FAILED
    private List<String> reservedProducts;
    private Instant timestamp;
}
