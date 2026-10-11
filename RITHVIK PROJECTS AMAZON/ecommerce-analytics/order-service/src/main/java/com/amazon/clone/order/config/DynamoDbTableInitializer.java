package com.amazon.clone.order.config;

import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.context.event.ApplicationReadyEvent;
import org.springframework.context.event.EventListener;
import org.springframework.stereotype.Component;
import software.amazon.awssdk.services.dynamodb.DynamoDbClient;
import software.amazon.awssdk.services.dynamodb.model.*;

/**
 * Runs after Spring context is ready to create DynamoDB table in LocalStack.
 * Separated from DynamoDbConfig to avoid circular @Bean self-reference.
 */
@Slf4j
@Component
public class DynamoDbTableInitializer {

    private final DynamoDbClient client;

    @Value("${aws.dynamodb.ordersTable}")
    private String ordersTable;

    public DynamoDbTableInitializer(DynamoDbClient client) {
        this.client = client;
    }

    @EventListener(ApplicationReadyEvent.class)
    public void createTableIfNotExists() {
        try {
            client.describeTable(DescribeTableRequest.builder().tableName(ordersTable).build());
            log.info("[DynamoDB] Table '{}' already exists.", ordersTable);
        } catch (ResourceNotFoundException e) {
            client.createTable(CreateTableRequest.builder()
                    .tableName(ordersTable)
                    .keySchema(
                            KeySchemaElement.builder().attributeName("orderId").keyType(KeyType.HASH).build(),
                            KeySchemaElement.builder().attributeName("userId").keyType(KeyType.RANGE).build())
                    .attributeDefinitions(
                            AttributeDefinition.builder().attributeName("orderId").attributeType(ScalarAttributeType.S).build(),
                            AttributeDefinition.builder().attributeName("userId").attributeType(ScalarAttributeType.S).build())
                    .billingMode(BillingMode.PAY_PER_REQUEST)
                    .build());
            log.info("[DynamoDB] Table '{}' created.", ordersTable);
        }
    }
}
