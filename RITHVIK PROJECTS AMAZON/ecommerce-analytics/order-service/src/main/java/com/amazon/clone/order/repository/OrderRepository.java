package com.amazon.clone.order.repository;

import com.amazon.clone.order.model.Order;
import org.springframework.stereotype.Repository;
import software.amazon.awssdk.enhanced.dynamodb.DynamoDbTable;
import software.amazon.awssdk.enhanced.dynamodb.Key;
import software.amazon.awssdk.enhanced.dynamodb.model.QueryConditional;

import java.util.List;
import java.util.Optional;
import java.util.stream.Collectors;

@Repository
public class OrderRepository {

    private final DynamoDbTable<Order> ordersTable;

    public OrderRepository(DynamoDbTable<Order> ordersTable) {
        this.ordersTable = ordersTable;
    }

    public Order save(Order order) {
        ordersTable.putItem(order);
        return order;
    }

    public Optional<Order> findById(String orderId, String userId) {
        Key key = Key.builder().partitionValue(orderId).sortValue(userId).build();
        return Optional.ofNullable(ordersTable.getItem(key));
    }

    public List<Order> findByOrderId(String orderId) {
        return ordersTable.query(QueryConditional.keyEqualTo(
                        Key.builder().partitionValue(orderId).build()))
                .items().stream().collect(Collectors.toList());
    }

    public void delete(String orderId, String userId) {
        Key key = Key.builder().partitionValue(orderId).sortValue(userId).build();
        ordersTable.deleteItem(key);
    }
}
