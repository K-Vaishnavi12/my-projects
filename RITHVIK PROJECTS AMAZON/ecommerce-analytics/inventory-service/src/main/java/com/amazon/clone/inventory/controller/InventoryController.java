package com.amazon.clone.inventory.controller;

import com.amazon.clone.inventory.service.InventoryService;
import org.springframework.web.bind.annotation.*;

import java.util.Map;

@RestController
@RequestMapping("/api/v1/inventory")
public class InventoryController {

    private final InventoryService service;

    public InventoryController(InventoryService service) { this.service = service; }

    @GetMapping("/{productId}")
    public Map<String, Object> get(@PathVariable String productId) {
        return Map.of("productId", productId, "stock", service.getStock(productId));
    }

    @GetMapping("/health")
    public Map<String, String> health() {
        return Map.of("status", "UP", "service", "inventory-service");
    }
}
