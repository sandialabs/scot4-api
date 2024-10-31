/* Run this after creating DB tables with helm chart */
/* Prepares tables for a migration of scot3 data by making sure only data that will be replaced is wiped */

TRUNCATE TABLE `links`;
TRUNCATE TABLE `object_permissions`;
TRUNCATE TABLE `promotions`;
TRUNCATE TABLE `alert_data`;
TRUNCATE TABLE `alertgroup_schema_keys`;
TRUNCATE TABLE `guides`;
TRUNCATE TABLE `alerts`;
TRUNCATE TABLE `alertgroups`;
TRUNCATE TABLE `dispatches`;
TRUNCATE TABLE `entities`;
TRUNCATE TABLE `entity_types`;
TRUNCATE TABLE `entries`;
TRUNCATE TABLE `events`;
TRUNCATE TABLE `incidents`;
TRUNCATE TABLE `intels`;
TRUNCATE TABLE `signatures`;
TRUNCATE TABLE `products`;
/* need to re-insert base roles after delete */
TRUNCATE TABLE `roles`;
INSERT INTO `roles` VALUES (1,'everyone',NULL,'2023-06-06 16:53:27','2023-06-06 16:53:27'),(2,'admin',NULL,'2023-06-06 16:53:27','2023-06-06 16:53:27');
TRUNCATE TABLE `handlers`;
TRUNCATE TABLE `sources`;
TRUNCATE TABLE `tags`;
TRUNCATE TABLE `enrichments`;
TRUNCATE TABLE `entity_class_entity_association`;
TRUNCATE TABLE `games`;