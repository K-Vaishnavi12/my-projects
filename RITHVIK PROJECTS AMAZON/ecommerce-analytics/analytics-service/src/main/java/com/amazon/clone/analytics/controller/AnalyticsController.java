package com.amazon.clone.analytics.controller;

import com.amazon.clone.analytics.service.AnalyticsService;
import org.springframework.web.bind.annotation.*;

import java.util.LinkedHashMap;
import java.util.Map;

@RestController
@RequestMapping("/api/v1/analytics")
public class AnalyticsController {

    private final AnalyticsService svc;

    public AnalyticsController(AnalyticsService svc) { this.svc = svc; }

    @GetMapping("/summary")
    public Map<String, Object> summary() {
        Map<String, Object> out = new LinkedHashMap<>();
        out.put("totalOrders", svc.totalOrders());
        out.put("totalRevenue", svc.totalRevenue());
        out.put("ordersLast1Min", svc.ordersInLastSeconds(60));
        out.put("ordersLast5Min", svc.ordersInLastSeconds(300));
        out.put("ordersLast1Hour", svc.ordersInLastSeconds(3600));
        out.put("topProducts", svc.topProducts(5));
        return out;
    }

    @GetMapping("/health")
    public Map<String, String> health() { return Map.of("status", "UP", "service", "analytics-service"); }
}
