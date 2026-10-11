package com.amazon.clone.order.model;

import lombok.Data;
import javax.validation.Valid;
import javax.validation.constraints.NotEmpty;
import javax.validation.constraints.NotNull;
import java.util.List;

@Data
public class CreateOrderRequest {

    @NotNull(message = "userId is required")
    private String userId;

    @NotEmpty(message = "items cannot be empty")
    @Valid
    private List<OrderItem> items;

    @NotNull(message = "shippingAddress is required")
    private String shippingAddress;
}
