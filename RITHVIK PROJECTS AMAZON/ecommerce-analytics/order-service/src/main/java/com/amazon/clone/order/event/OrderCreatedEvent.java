package com.amazon.clone.order.event;

import com.amazon.clone.order.model.Order;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.io.Serializable;
import java.time.Instant;

@Data
@NoArgsConstructor
@AllArgsConstructor
public class OrderCreatedEvent implements Serializable {
    private String eventId;
    private String orderId;
    private String userId;
    private Order order;
    private Instant timestamp;
}
