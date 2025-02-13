-- MySQL dump 10.13  Distrib 8.0.31, for Linux (x86_64)
--
-- ------------------------------------------------------
-- Server version	8.0.31

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;


--
-- Table structure for table `alert_data`
--

DROP TABLE IF EXISTS `alert_data`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `alert_data` (
  `schema_key_id` int NOT NULL,
  `alert_id` int NOT NULL,
  `data_value` mediumtext DEFAULT NULL,
  `data_value_flaired` mediumtext DEFAULT NULL,
  PRIMARY KEY (`schema_key_id`,`alert_id`),
  KEY `alert_id` (`alert_id`),
  CONSTRAINT `alert_data_ibfk_1` FOREIGN KEY (`schema_key_id`) REFERENCES `alertgroup_schema_keys` (`schema_key_id`),
  CONSTRAINT `alert_data_ibfk_2` FOREIGN KEY (`alert_id`) REFERENCES `alerts` (`alert_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `alert_data`
--

LOCK TABLES `alert_data` WRITE;
/*!40000 ALTER TABLE `alert_data` DISABLE KEYS */;
/*!40000 ALTER TABLE `alert_data` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `alertgroup_schema_keys`
--

DROP TABLE IF EXISTS `alertgroup_schema_keys`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `alertgroup_schema_keys` (
  `schema_key_id` int NOT NULL AUTO_INCREMENT,
  `schema_key_name` text,
  `schema_key_type` text,
  `schema_key_order` int NOT NULL,
  `alertgroup_id` int DEFAULT NULL,
  PRIMARY KEY (`schema_key_id`),
  KEY `alertgroup_id` (`alertgroup_id`),
  CONSTRAINT `alertgroup_schema_keys_ibfk_1` FOREIGN KEY (`alertgroup_id`) REFERENCES `alertgroups` (`alertgroup_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `alertgroup_schema_keys`
--

LOCK TABLES `alertgroup_schema_keys` WRITE;
/*!40000 ALTER TABLE `alertgroup_schema_keys` DISABLE KEYS */;
/*!40000 ALTER TABLE `alertgroup_schema_keys` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `alertgroups`
--

DROP TABLE IF EXISTS `alertgroups`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `alertgroups` (
  `alertgroup_id` int NOT NULL AUTO_INCREMENT,
  `owner` text NOT NULL,
  `tlp` enum('unset','white','green','amber','red','black','clear','amber_strict') DEFAULT NULL,
  `view_count` int NOT NULL,
  `firstview_date` datetime DEFAULT NULL,
  `message_id` text,
  `subject` text,
  `backrefs` text,
  `created_date` datetime DEFAULT NULL,
  `modified_date` datetime NOT NULL,
  PRIMARY KEY (`alertgroup_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `alertgroups`
--

LOCK TABLES `alertgroups` WRITE;
/*!40000 ALTER TABLE `alertgroups` DISABLE KEYS */;
/*!40000 ALTER TABLE `alertgroups` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `alerts`
--

DROP TABLE IF EXISTS `alerts`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `alerts` (
  `alert_id` int NOT NULL AUTO_INCREMENT,
  `owner` varchar(320) NOT NULL DEFAULT 'scot-admin',
  `tlp` enum('unset','white','green','amber','red','black','clear','amber_strict') NOT NULL DEFAULT 'unset',
  `status` enum('open','promoted','closed') NOT NULL DEFAULT 'open',
  `parsed` tinyint(1) NOT NULL DEFAULT '0',
  `alertgroup_id` int NOT NULL,
  `created_date` datetime DEFAULT NULL,
  `modified_date` datetime NOT NULL,
  PRIMARY KEY (`alert_id`),
  KEY `alertgroup_id` (`alertgroup_id`),
  CONSTRAINT `alerts_ibfk_1` FOREIGN KEY (`alertgroup_id`) REFERENCES `alertgroups` (`alertgroup_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `alerts`
--

LOCK TABLES `alerts` WRITE;
/*!40000 ALTER TABLE `alerts` DISABLE KEYS */;
/*!40000 ALTER TABLE `alerts` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `apikeys`
--

DROP TABLE IF EXISTS `apikeys`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `apikeys` (
  `key` varchar(255) NOT NULL,
  `owner` varchar(255) NOT NULL,
  `active` tinyint(1) NOT NULL DEFAULT '1',
  PRIMARY KEY (`key`),
  KEY `owner` (`owner`),
  CONSTRAINT `apikeys_ibfk_1` FOREIGN KEY (`owner`) REFERENCES `users` (`username`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `apikeys`
--

LOCK TABLES `apikeys` WRITE;
/*!40000 ALTER TABLE `apikeys` DISABLE KEYS */;
/*!40000 ALTER TABLE `apikeys` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `apikeys_roles`
--

DROP TABLE IF EXISTS `apikeys_roles`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `apikeys_roles` (
  `key` varchar(255) DEFAULT NULL,
  `role_id` int DEFAULT NULL,
  KEY `key` (`key`),
  KEY `role_id` (`role_id`),
  CONSTRAINT `apikeys_roles_ibfk_1` FOREIGN KEY (`key`) REFERENCES `apikeys` (`key`),
  CONSTRAINT `apikeys_roles_ibfk_2` FOREIGN KEY (`role_id`) REFERENCES `roles` (`role_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `apikeys_roles`
--

LOCK TABLES `apikeys_roles` WRITE;
/*!40000 ALTER TABLE `apikeys_roles` DISABLE KEYS */;
/*!40000 ALTER TABLE `apikeys_roles` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `appearances`
--

DROP TABLE IF EXISTS `appearances`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `appearances` (
  `appearance_id` int NOT NULL AUTO_INCREMENT,
  `when_date` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `target_id` int DEFAULT NULL,
  `target_type` enum('alert','alertgroup','checklist','dispatch','entity','entry','event','file','guide','incident','intel','product','sigbody','signature','entity_class','entity_type','source','stat','tag','admin','threat_model_item','feed','pivot','none') DEFAULT NULL,
  `value_id` int DEFAULT NULL,
  `value_type` text,
  `value_str` text,
  PRIMARY KEY (`appearance_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `appearances`
--

LOCK TABLES `appearances` WRITE;
/*!40000 ALTER TABLE `appearances` DISABLE KEYS */;
/*!40000 ALTER TABLE `appearances` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `audits`
--

DROP TABLE IF EXISTS `audits`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `audits` (
  `audit_id` int NOT NULL AUTO_INCREMENT,
  `when_date` datetime NOT NULL,
  `username` text,
  `what` text NOT NULL,
  `thing_type` text,
  `thing_subtype` text,
  `thing_id` int DEFAULT NULL,
  `src_ip` text,
  `user_agent` text,
  `audit_data_ver` text,
  `audit_data` json DEFAULT NULL,
  PRIMARY KEY (`audit_id`),
  KEY `audit_speedup_1` (`what`(16)),
  KEY `audit_speedup_2` (`thing_type`(16),`thing_id`),
  KEY `audit_speedup_3` (`username`(16)),
  KEY `audit_speedup_4` (`when_date`),
  KEY `game_speedup_1` (((cast(json_unquote(json_extract(`audit_data`,_utf8mb4'$.p0_type')) as char(16) charset utf8mb4) collate utf8mb4_bin))),
  KEY `game_speedup_2` (((cast(json_unquote(json_extract(`audit_data`,_utf8mb4'$.p1_type')) as char(16) charset utf8mb4) collate utf8mb4_bin))),
  KEY `game_speedup_3` (((cast(json_unquote(json_extract(`audit_data`,_utf8mb4'$.status')) as char(16) charset utf8mb4) collate utf8mb4_bin))),
  KEY `game_speedup_4` (((cast(json_unquote(json_extract(`audit_data`,_utf8mb4'$.target_type')) as char(16) charset utf8mb4) collate utf8mb4_bin)))
) ENGINE=InnoDB AUTO_INCREMENT=16000478 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `audits`
--

LOCK TABLES `audits` WRITE;
/*!40000 ALTER TABLE `audits` DISABLE KEYS */;
/*!40000 ALTER TABLE `audits` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `auth_settings`
--

DROP TABLE IF EXISTS `auth_settings`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `auth_settings` (
  `auth_settings_id` int NOT NULL AUTO_INCREMENT,
  `auth` enum('ldap','local','aad') COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `auth_properties` json DEFAULT NULL,
  `auth_active` tinyint(1) DEFAULT NULL,
  `created_date` datetime DEFAULT NULL,
  `modified_date` datetime NOT NULL,
  PRIMARY KEY (`auth_settings_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

LOCK TABLES `auth_settings` WRITE;
INSERT INTO `auth_settings` VALUES (1, 'local', '{}', 1, '2023-06-06 16:53:27','2023-06-06 16:53:27');
UNLOCK TABLES;

--
-- Table structure for table `auth_storage`
--

DROP TABLE IF EXISTS `auth_storage`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `auth_storage` (
  `auth_storage_id` int NOT NULL AUTO_INCREMENT,
  `key` text COLLATE utf8mb4_unicode_ci,
  `value` text COLLATE utf8mb4_unicode_ci,
  `auth_settings_id` int DEFAULT NULL,
  PRIMARY KEY (`auth_storage_id`),
  KEY `auth_settings_id` (`auth_settings_id`),
  CONSTRAINT `auth_storage_ibfk_1` FOREIGN KEY (`auth_settings_id`) REFERENCES `auth_settings` (`auth_settings_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `checklists`
--

DROP TABLE IF EXISTS `checklists`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `checklists` (
  `checklist_id` int NOT NULL AUTO_INCREMENT,
  `owner` text NOT NULL,
  `tlp` enum('unset','white','green','amber','red','black','clear','amber_strict') NOT NULL,
  `subject` text,
  `checklist_data_ver` text,
  `checklist_data` json DEFAULT NULL,
  `created_date` datetime DEFAULT NULL,
  `modified_date` datetime NOT NULL,
  PRIMARY KEY (`checklist_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `checklists`
--

LOCK TABLES `checklists` WRITE;
/*!40000 ALTER TABLE `checklists` DISABLE KEYS */;
/*!40000 ALTER TABLE `checklists` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `dispatches`
--

DROP TABLE IF EXISTS `dispatches`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `dispatches` (
  `dispatches_id` int NOT NULL AUTO_INCREMENT,
  `owner` text NOT NULL,
  `tlp` enum('unset','white','green','amber','red','black','clear','amber_strict') NOT NULL,
  `subject` text,
  `status` enum('open','promoted','closed') DEFAULT NULL,
  `message_id` text,
  `created_date` datetime DEFAULT NULL,
  `modified_date` datetime NOT NULL,
  PRIMARY KEY (`dispatches_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `dispatches`
--

LOCK TABLES `dispatches` WRITE;
/*!40000 ALTER TABLE `dispatches` DISABLE KEYS */;
/*!40000 ALTER TABLE `dispatches` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `enrichments`
--

DROP TABLE IF EXISTS `enrichments`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `enrichments` (
  `enrichment_id` int NOT NULL AUTO_INCREMENT,
  `entity_id` int DEFAULT NULL,
  `enrichment_title` text NOT NULL,
  `enrichment_class` enum('markdown','linechart','jsontree','plaintext') DEFAULT NULL,
  `enrichment_data` json DEFAULT NULL,
  `enrichment_description` text,
  `created_date` datetime DEFAULT NULL,
  `modified_date` datetime NOT NULL,
  PRIMARY KEY (`enrichment_id`),
  KEY `entity_id` (`entity_id`),
  CONSTRAINT `enrichments_ibfk_1` FOREIGN KEY (`entity_id`) REFERENCES `entities` (`entity_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `enrichments`
--

LOCK TABLES `enrichments` WRITE;
/*!40000 ALTER TABLE `enrichments` DISABLE KEYS */;
/*!40000 ALTER TABLE `enrichments` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `entities`
--

DROP TABLE IF EXISTS `entities`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `entities` (
  `entity_id` int NOT NULL AUTO_INCREMENT,
  `status` enum('tracked','untracked') DEFAULT NULL,
  `entity_value` text,
  `type_id` int DEFAULT NULL,
  `entity_data_ver` text,
  `entity_data` json DEFAULT NULL,
  `created_date` datetime DEFAULT NULL,
  `modified_date` datetime NOT NULL,
  PRIMARY KEY (`entity_id`),
  KEY `type_id` (`type_id`),
  KEY `entity_lookup` (`entity_value`(16)),
  KEY `enrichment_lookup` (`entity_value`(16)),
  CONSTRAINT `entities_ibfk_1` FOREIGN KEY (`type_id`) REFERENCES `entity_types` (`entity_type_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `entities`
--

LOCK TABLES `entities` WRITE;
/*!40000 ALTER TABLE `entities` DISABLE KEYS */;
/*!40000 ALTER TABLE `entities` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `entity_class_entity_association`
--

DROP TABLE IF EXISTS `entity_class_entity_association`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `entity_class_entity_association` (
  `entity_id` int DEFAULT NULL,
  `entity_class_id` int DEFAULT NULL,
  KEY `entity_id` (`entity_id`),
  KEY `entity_class_id` (`entity_class_id`),
  CONSTRAINT `entity_class_entity_association_ibfk_1` FOREIGN KEY (`entity_id`) REFERENCES `entities` (`entity_id`),
  CONSTRAINT `entity_class_entity_association_ibfk_2` FOREIGN KEY (`entity_class_id`) REFERENCES `entity_classes` (`entity_class_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `entity_class_entity_association`
--

LOCK TABLES `entity_class_entity_association` WRITE;
/*!40000 ALTER TABLE `entity_class_entity_association` DISABLE KEYS */;
/*!40000 ALTER TABLE `entity_class_entity_association` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `entity_classes`
--

DROP TABLE IF EXISTS `entity_classes`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `entity_classes` (
  `entity_class_id` int NOT NULL AUTO_INCREMENT,
  `entity_class_name` varchar(320) DEFAULT NULL,
  `entity_class_display_name` varchar(320) DEFAULT NULL,
  `entity_class_description` text,
  `entity_icon` text,
  `entity_class_data` json DEFAULT NULL,
  `created_date` datetime DEFAULT NULL,
  `modified_date` datetime NOT NULL,
  PRIMARY KEY (`entity_class_id`),
  UNIQUE KEY `entity_class_name` (`entity_class_name`)
) ENGINE=InnoDB AUTO_INCREMENT=265 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `entity_classes`
--

LOCK TABLES `entity_classes` WRITE;
/*!40000 ALTER TABLE `entity_classes` DISABLE KEYS */;
INSERT INTO `entity_classes` VALUES (1,'ad_flag','Andorra','Denotes that this entity is associated geographically to the country: Andorra','$vuetify.icons.ad_flag',NULL,'2023-06-06 16:53:28','2023-06-06 16:53:28'),(2,'ae_flag','United Arab Emirates','Denotes that this entity is associated geographically to the country: United Arab Emirates','$vuetify.icons.ae_flag',NULL,'2023-06-06 16:53:28','2023-06-06 16:53:28'),(3,'af_flag','Afghanistan','Denotes that this entity is associated geographically to the country: Afghanistan','$vuetify.icons.af_flag',NULL,'2023-06-06 16:53:28','2023-06-06 16:53:28'),(4,'ag_flag','Antigua and Barbuda','Denotes that this entity is associated geographically to the country: Antigua and Barbuda','$vuetify.icons.ag_flag',NULL,'2023-06-06 16:53:28','2023-06-06 16:53:28'),(5,'ai_flag','Anguilla','Denotes that this entity is associated geographically to the country: Anguilla','$vuetify.icons.ai_flag',NULL,'2023-06-06 16:53:28','2023-06-06 16:53:28'),(6,'al_flag','Albania','Denotes that this entity is associated geographically to the country: Albania','$vuetify.icons.al_flag',NULL,'2023-06-06 16:53:28','2023-06-06 16:53:28'),(7,'am_flag','Armenia','Denotes that this entity is associated geographically to the country: Armenia','$vuetify.icons.am_flag',NULL,'2023-06-06 16:53:28','2023-06-06 16:53:28'),(8,'ao_flag','Angola','Denotes that this entity is associated geographically to the country: Angola','$vuetify.icons.ao_flag',NULL,'2023-06-06 16:53:28','2023-06-06 16:53:28'),(9,'aq_flag','Antarctica','Denotes that this entity is associated geographically to the country: Antarctica','$vuetify.icons.aq_flag',NULL,'2023-06-06 16:53:28','2023-06-06 16:53:28'),(10,'ar_flag','Argentina','Denotes that this entity is associated geographically to the country: Argentina','$vuetify.icons.ar_flag',NULL,'2023-06-06 16:53:28','2023-06-06 16:53:28'),(11,'as_flag','American Samoa','Denotes that this entity is associated geographically to the country: American Samoa','$vuetify.icons.as_flag',NULL,'2023-06-06 16:53:28','2023-06-06 16:53:28'),(12,'at_flag','Austria','Denotes that this entity is associated geographically to the country: Austria','$vuetify.icons.at_flag',NULL,'2023-06-06 16:53:28','2023-06-06 16:53:28'),(13,'au_flag','Australia','Denotes that this entity is associated geographically to the country: Australia','$vuetify.icons.au_flag',NULL,'2023-06-06 16:53:28','2023-06-06 16:53:28'),(14,'aw_flag','Aruba','Denotes that this entity is associated geographically to the country: Aruba','$vuetify.icons.aw_flag',NULL,'2023-06-06 16:53:28','2023-06-06 16:53:28'),(15,'ax_flag','Aland Islands','Denotes that this entity is associated geographically to the country: Aland Islands','$vuetify.icons.ax_flag',NULL,'2023-06-06 16:53:28','2023-06-06 16:53:28'),(16,'az_flag','Azerbaijan','Denotes that this entity is associated geographically to the country: Azerbaijan','$vuetify.icons.az_flag',NULL,'2023-06-06 16:53:28','2023-06-06 16:53:28'),(17,'ba_flag','Bosnia and Herzegovina','Denotes that this entity is associated geographically to the country: Bosnia and Herzegovina','$vuetify.icons.ba_flag',NULL,'2023-06-06 16:53:28','2023-06-06 16:53:28'),(18,'bb_flag','Barbados','Denotes that this entity is associated geographically to the country: Barbados','$vuetify.icons.bb_flag',NULL,'2023-06-06 16:53:28','2023-06-06 16:53:28'),(19,'bd_flag','Bangladesh','Denotes that this entity is associated geographically to the country: Bangladesh','$vuetify.icons.bd_flag',NULL,'2023-06-06 16:53:28','2023-06-06 16:53:28'),(20,'be_flag','Belgium','Denotes that this entity is associated geographically to the country: Belgium','$vuetify.icons.be_flag',NULL,'2023-06-06 16:53:28','2023-06-06 16:53:28'),(21,'bf_flag','Burkina Faso','Denotes that this entity is associated geographically to the country: Burkina Faso','$vuetify.icons.bf_flag',NULL,'2023-06-06 16:53:28','2023-06-06 16:53:28'),(22,'bg_flag','Bulgaria','Denotes that this entity is associated geographically to the country: Bulgaria','$vuetify.icons.bg_flag',NULL,'2023-06-06 16:53:28','2023-06-06 16:53:28'),(23,'bh_flag','Bahrain','Denotes that this entity is associated geographically to the country: Bahrain','$vuetify.icons.bh_flag',NULL,'2023-06-06 16:53:28','2023-06-06 16:53:28'),(24,'bi_flag','Burundi','Denotes that this entity is associated geographically to the country: Burundi','$vuetify.icons.bi_flag',NULL,'2023-06-06 16:53:28','2023-06-06 16:53:28'),(25,'bj_flag','Benin','Denotes that this entity is associated geographically to the country: Benin','$vuetify.icons.bj_flag',NULL,'2023-06-06 16:53:28','2023-06-06 16:53:28'),(26,'bl_flag','Saint Barthélemy','Denotes that this entity is associated geographically to the country: Saint Barthélemy','$vuetify.icons.bl_flag',NULL,'2023-06-06 16:53:28','2023-06-06 16:53:28'),(27,'bm_flag','Bermuda','Denotes that this entity is associated geographically to the country: Bermuda','$vuetify.icons.bm_flag',NULL,'2023-06-06 16:53:28','2023-06-06 16:53:28'),(28,'bn_flag','Brunei Darussalam','Denotes that this entity is associated geographically to the country: Brunei Darussalam','$vuetify.icons.bn_flag',NULL,'2023-06-06 16:53:28','2023-06-06 16:53:28'),(29,'bo_flag','Bolivia (Plurinational State of)','Denotes that this entity is associated geographically to the country: Bolivia (Plurinational State of)','$vuetify.icons.bo_flag',NULL,'2023-06-06 16:53:28','2023-06-06 16:53:28'),(30,'bq_flag','Bonaire, Sint Eustatius and Saba','Denotes that this entity is associated geographically to the country: Bonaire, Sint Eustatius and Saba','$vuetify.icons.bq_flag',NULL,'2023-06-06 16:53:28','2023-06-06 16:53:28'),(31,'br_flag','Brazil','Denotes that this entity is associated geographically to the country: Brazil','$vuetify.icons.br_flag',NULL,'2023-06-06 16:53:28','2023-06-06 16:53:28'),(32,'bs_flag','Bahamas','Denotes that this entity is associated geographically to the country: Bahamas','$vuetify.icons.bs_flag',NULL,'2023-06-06 16:53:28','2023-06-06 16:53:28'),(33,'bt_flag','Bhutan','Denotes that this entity is associated geographically to the country: Bhutan','$vuetify.icons.bt_flag',NULL,'2023-06-06 16:53:28','2023-06-06 16:53:28'),(34,'bv_flag','Bouvet Island','Denotes that this entity is associated geographically to the country: Bouvet Island','$vuetify.icons.bv_flag',NULL,'2023-06-06 16:53:28','2023-06-06 16:53:28'),(35,'bw_flag','Botswana','Denotes that this entity is associated geographically to the country: Botswana','$vuetify.icons.bw_flag',NULL,'2023-06-06 16:53:28','2023-06-06 16:53:28'),(36,'by_flag','Belarus','Denotes that this entity is associated geographically to the country: Belarus','$vuetify.icons.by_flag',NULL,'2023-06-06 16:53:28','2023-06-06 16:53:28'),(37,'bz_flag','Belize','Denotes that this entity is associated geographically to the country: Belize','$vuetify.icons.bz_flag',NULL,'2023-06-06 16:53:28','2023-06-06 16:53:28'),(38,'ca_flag','Canada','Denotes that this entity is associated geographically to the country: Canada','$vuetify.icons.ca_flag',NULL,'2023-06-06 16:53:28','2023-06-06 16:53:28'),(39,'cc_flag','Cocos (Keeling) Islands','Denotes that this entity is associated geographically to the country: Cocos (Keeling) Islands','$vuetify.icons.cc_flag',NULL,'2023-06-06 16:53:28','2023-06-06 16:53:28'),(40,'cd_flag','Democratic Republic of the Congo','Denotes that this entity is associated geographically to the country: Democratic Republic of the Congo','$vuetify.icons.cd_flag',NULL,'2023-06-06 16:53:28','2023-06-06 16:53:28'),(41,'cf_flag','Central African Republic','Denotes that this entity is associated geographically to the country: Central African Republic','$vuetify.icons.cf_flag',NULL,'2023-06-06 16:53:28','2023-06-06 16:53:28'),(42,'cg_flag','Republic of the Congo','Denotes that this entity is associated geographically to the country: Republic of the Congo','$vuetify.icons.cg_flag',NULL,'2023-06-06 16:53:28','2023-06-06 16:53:28'),(43,'ch_flag','Switzerland','Denotes that this entity is associated geographically to the country: Switzerland','$vuetify.icons.ch_flag',NULL,'2023-06-06 16:53:28','2023-06-06 16:53:28'),(44,'ci_flag','Côte d\'Ivoire','Denotes that this entity is associated geographically to the country: Côte d\'Ivoire','$vuetify.icons.ci_flag',NULL,'2023-06-06 16:53:28','2023-06-06 16:53:28'),(45,'ck_flag','Cook Islands','Denotes that this entity is associated geographically to the country: Cook Islands','$vuetify.icons.ck_flag',NULL,'2023-06-06 16:53:28','2023-06-06 16:53:28'),(46,'cl_flag','Chile','Denotes that this entity is associated geographically to the country: Chile','$vuetify.icons.cl_flag',NULL,'2023-06-06 16:53:28','2023-06-06 16:53:28'),(47,'cm_flag','Cameroon','Denotes that this entity is associated geographically to the country: Cameroon','$vuetify.icons.cm_flag',NULL,'2023-06-06 16:53:28','2023-06-06 16:53:28'),(48,'cn_flag','China','Denotes that this entity is associated geographically to the country: China','$vuetify.icons.cn_flag',NULL,'2023-06-06 16:53:28','2023-06-06 16:53:28'),(49,'co_flag','Colombia','Denotes that this entity is associated geographically to the country: Colombia','$vuetify.icons.co_flag',NULL,'2023-06-06 16:53:28','2023-06-06 16:53:28'),(50,'cr_flag','Costa Rica','Denotes that this entity is associated geographically to the country: Costa Rica','$vuetify.icons.cr_flag',NULL,'2023-06-06 16:53:28','2023-06-06 16:53:28'),(51,'cu_flag','Cuba','Denotes that this entity is associated geographically to the country: Cuba','$vuetify.icons.cu_flag',NULL,'2023-06-06 16:53:28','2023-06-06 16:53:28'),(52,'cv_flag','Cabo Verde','Denotes that this entity is associated geographically to the country: Cabo Verde','$vuetify.icons.cv_flag',NULL,'2023-06-06 16:53:28','2023-06-06 16:53:28'),(53,'cw_flag','Curaçao','Denotes that this entity is associated geographically to the country: Curaçao','$vuetify.icons.cw_flag',NULL,'2023-06-06 16:53:28','2023-06-06 16:53:28'),(54,'cx_flag','Christmas Island','Denotes that this entity is associated geographically to the country: Christmas Island','$vuetify.icons.cx_flag',NULL,'2023-06-06 16:53:28','2023-06-06 16:53:28'),(55,'cy_flag','Cyprus','Denotes that this entity is associated geographically to the country: Cyprus','$vuetify.icons.cy_flag',NULL,'2023-06-06 16:53:28','2023-06-06 16:53:28'),(56,'cz_flag','Czech Republic','Denotes that this entity is associated geographically to the country: Czech Republic','$vuetify.icons.cz_flag',NULL,'2023-06-06 16:53:28','2023-06-06 16:53:28'),(57,'de_flag','Germany','Denotes that this entity is associated geographically to the country: Germany','$vuetify.icons.de_flag',NULL,'2023-06-06 16:53:28','2023-06-06 16:53:28'),(58,'dj_flag','Djibouti','Denotes that this entity is associated geographically to the country: Djibouti','$vuetify.icons.dj_flag',NULL,'2023-06-06 16:53:28','2023-06-06 16:53:28'),(59,'dk_flag','Denmark','Denotes that this entity is associated geographically to the country: Denmark','$vuetify.icons.dk_flag',NULL,'2023-06-06 16:53:28','2023-06-06 16:53:28'),(60,'dm_flag','Dominica','Denotes that this entity is associated geographically to the country: Dominica','$vuetify.icons.dm_flag',NULL,'2023-06-06 16:53:28','2023-06-06 16:53:28'),(61,'do_flag','Dominican Republic','Denotes that this entity is associated geographically to the country: Dominican Republic','$vuetify.icons.do_flag',NULL,'2023-06-06 16:53:28','2023-06-06 16:53:28'),(62,'dz_flag','Algeria','Denotes that this entity is associated geographically to the country: Algeria','$vuetify.icons.dz_flag',NULL,'2023-06-06 16:53:28','2023-06-06 16:53:28'),(63,'ec_flag','Ecuador','Denotes that this entity is associated geographically to the country: Ecuador','$vuetify.icons.ec_flag',NULL,'2023-06-06 16:53:28','2023-06-06 16:53:28'),(64,'ee_flag','Estonia','Denotes that this entity is associated geographically to the country: Estonia','$vuetify.icons.ee_flag',NULL,'2023-06-06 16:53:28','2023-06-06 16:53:28'),(65,'eg_flag','Egypt','Denotes that this entity is associated geographically to the country: Egypt','$vuetify.icons.eg_flag',NULL,'2023-06-06 16:53:28','2023-06-06 16:53:28'),(66,'eh_flag','Western Sahara','Denotes that this entity is associated geographically to the country: Western Sahara','$vuetify.icons.eh_flag',NULL,'2023-06-06 16:53:28','2023-06-06 16:53:28'),(67,'er_flag','Eritrea','Denotes that this entity is associated geographically to the country: Eritrea','$vuetify.icons.er_flag',NULL,'2023-06-06 16:53:28','2023-06-06 16:53:28'),(68,'es_flag','Spain','Denotes that this entity is associated geographically to the country: Spain','$vuetify.icons.es_flag',NULL,'2023-06-06 16:53:28','2023-06-06 16:53:28'),(69,'et_flag','Ethiopia','Denotes that this entity is associated geographically to the country: Ethiopia','$vuetify.icons.et_flag',NULL,'2023-06-06 16:53:28','2023-06-06 16:53:28'),(70,'fi_flag','Finland','Denotes that this entity is associated geographically to the country: Finland','$vuetify.icons.fi_flag',NULL,'2023-06-06 16:53:28','2023-06-06 16:53:28'),(71,'fj_flag','Fiji','Denotes that this entity is associated geographically to the country: Fiji','$vuetify.icons.fj_flag',NULL,'2023-06-06 16:53:28','2023-06-06 16:53:28'),(72,'fk_flag','Falkland Islands','Denotes that this entity is associated geographically to the country: Falkland Islands','$vuetify.icons.fk_flag',NULL,'2023-06-06 16:53:28','2023-06-06 16:53:28'),(73,'fm_flag','Federated States of Micronesia','Denotes that this entity is associated geographically to the country: Federated States of Micronesia','$vuetify.icons.fm_flag',NULL,'2023-06-06 16:53:28','2023-06-06 16:53:28'),(74,'fo_flag','Faroe Islands','Denotes that this entity is associated geographically to the country: Faroe Islands','$vuetify.icons.fo_flag',NULL,'2023-06-06 16:53:28','2023-06-06 16:53:28'),(75,'fr_flag','France','Denotes that this entity is associated geographically to the country: France','$vuetify.icons.fr_flag',NULL,'2023-06-06 16:53:28','2023-06-06 16:53:28'),(76,'ga_flag','Gabon','Denotes that this entity is associated geographically to the country: Gabon','$vuetify.icons.ga_flag',NULL,'2023-06-06 16:53:28','2023-06-06 16:53:28'),(77,'gb_flag','United Kingdom','Denotes that this entity is associated geographically to the country: United Kingdom','$vuetify.icons.gb_flag',NULL,'2023-06-06 16:53:28','2023-06-06 16:53:28'),(78,'gd_flag','Grenada','Denotes that this entity is associated geographically to the country: Grenada','$vuetify.icons.gd_flag',NULL,'2023-06-06 16:53:28','2023-06-06 16:53:28'),(79,'ge_flag','Georgia','Denotes that this entity is associated geographically to the country: Georgia','$vuetify.icons.ge_flag',NULL,'2023-06-06 16:53:28','2023-06-06 16:53:28'),(80,'gf_flag','French Guiana','Denotes that this entity is associated geographically to the country: French Guiana','$vuetify.icons.gf_flag',NULL,'2023-06-06 16:53:28','2023-06-06 16:53:28'),(81,'gg_flag','Guernsey','Denotes that this entity is associated geographically to the country: Guernsey','$vuetify.icons.gg_flag',NULL,'2023-06-06 16:53:28','2023-06-06 16:53:28'),(82,'gh_flag','Ghana','Denotes that this entity is associated geographically to the country: Ghana','$vuetify.icons.gh_flag',NULL,'2023-06-06 16:53:28','2023-06-06 16:53:28'),(83,'gi_flag','Gibraltar','Denotes that this entity is associated geographically to the country: Gibraltar','$vuetify.icons.gi_flag',NULL,'2023-06-06 16:53:28','2023-06-06 16:53:28'),(84,'gl_flag','Greenland','Denotes that this entity is associated geographically to the country: Greenland','$vuetify.icons.gl_flag',NULL,'2023-06-06 16:53:28','2023-06-06 16:53:28'),(85,'gm_flag','Gambia','Denotes that this entity is associated geographically to the country: Gambia','$vuetify.icons.gm_flag',NULL,'2023-06-06 16:53:28','2023-06-06 16:53:28'),(86,'gn_flag','Guinea','Denotes that this entity is associated geographically to the country: Guinea','$vuetify.icons.gn_flag',NULL,'2023-06-06 16:53:28','2023-06-06 16:53:28'),(87,'gp_flag','Guadeloupe','Denotes that this entity is associated geographically to the country: Guadeloupe','$vuetify.icons.gp_flag',NULL,'2023-06-06 16:53:28','2023-06-06 16:53:28'),(88,'gq_flag','Equatorial Guinea','Denotes that this entity is associated geographically to the country: Equatorial Guinea','$vuetify.icons.gq_flag',NULL,'2023-06-06 16:53:28','2023-06-06 16:53:28'),(89,'gr_flag','Greece','Denotes that this entity is associated geographically to the country: Greece','$vuetify.icons.gr_flag',NULL,'2023-06-06 16:53:28','2023-06-06 16:53:28'),(90,'gs_flag','South Georgia and the South Sandwich Islands','Denotes that this entity is associated geographically to the country: South Georgia and the South Sandwich Islands','$vuetify.icons.gs_flag',NULL,'2023-06-06 16:53:28','2023-06-06 16:53:28'),(91,'gt_flag','Guatemala','Denotes that this entity is associated geographically to the country: Guatemala','$vuetify.icons.gt_flag',NULL,'2023-06-06 16:53:28','2023-06-06 16:53:28'),(92,'gu_flag','Guam','Denotes that this entity is associated geographically to the country: Guam','$vuetify.icons.gu_flag',NULL,'2023-06-06 16:53:28','2023-06-06 16:53:28'),(93,'gw_flag','Guinea-Bissau','Denotes that this entity is associated geographically to the country: Guinea-Bissau','$vuetify.icons.gw_flag',NULL,'2023-06-06 16:53:28','2023-06-06 16:53:28'),(94,'gy_flag','Guyana','Denotes that this entity is associated geographically to the country: Guyana','$vuetify.icons.gy_flag',NULL,'2023-06-06 16:53:28','2023-06-06 16:53:28'),(95,'hk_flag','Hong Kong','Denotes that this entity is associated geographically to the country: Hong Kong','$vuetify.icons.hk_flag',NULL,'2023-06-06 16:53:28','2023-06-06 16:53:28'),(96,'hm_flag','Heard Island and McDonald Islands','Denotes that this entity is associated geographically to the country: Heard Island and McDonald Islands','$vuetify.icons.hm_flag',NULL,'2023-06-06 16:53:28','2023-06-06 16:53:28'),(97,'hn_flag','Honduras','Denotes that this entity is associated geographically to the country: Honduras','$vuetify.icons.hn_flag',NULL,'2023-06-06 16:53:28','2023-06-06 16:53:28'),(98,'hr_flag','Croatia','Denotes that this entity is associated geographically to the country: Croatia','$vuetify.icons.hr_flag',NULL,'2023-06-06 16:53:28','2023-06-06 16:53:28'),(99,'ht_flag','Haiti','Denotes that this entity is associated geographically to the country: Haiti','$vuetify.icons.ht_flag',NULL,'2023-06-06 16:53:28','2023-06-06 16:53:28'),(100,'hu_flag','Hungary','Denotes that this entity is associated geographically to the country: Hungary','$vuetify.icons.hu_flag',NULL,'2023-06-06 16:53:28','2023-06-06 16:53:28'),(101,'id_flag','Indonesia','Denotes that this entity is associated geographically to the country: Indonesia','$vuetify.icons.id_flag',NULL,'2023-06-06 16:53:28','2023-06-06 16:53:28'),(102,'ie_flag','Ireland','Denotes that this entity is associated geographically to the country: Ireland','$vuetify.icons.ie_flag',NULL,'2023-06-06 16:53:28','2023-06-06 16:53:28'),(103,'il_flag','Israel','Denotes that this entity is associated geographically to the country: Israel','$vuetify.icons.il_flag',NULL,'2023-06-06 16:53:28','2023-06-06 16:53:28'),(104,'im_flag','Isle of Man','Denotes that this entity is associated geographically to the country: Isle of Man','$vuetify.icons.im_flag',NULL,'2023-06-06 16:53:28','2023-06-06 16:53:28'),(105,'in_flag','India','Denotes that this entity is associated geographically to the country: India','$vuetify.icons.in_flag',NULL,'2023-06-06 16:53:28','2023-06-06 16:53:28'),(106,'io_flag','British Indian Ocean Territory','Denotes that this entity is associated geographically to the country: British Indian Ocean Territory','$vuetify.icons.io_flag',NULL,'2023-06-06 16:53:28','2023-06-06 16:53:28'),(107,'iq_flag','Iraq','Denotes that this entity is associated geographically to the country: Iraq','$vuetify.icons.iq_flag',NULL,'2023-06-06 16:53:28','2023-06-06 16:53:28'),(108,'ir_flag','Iran (Islamic Republic of)','Denotes that this entity is associated geographically to the country: Iran (Islamic Republic of)','$vuetify.icons.ir_flag',NULL,'2023-06-06 16:53:28','2023-06-06 16:53:28'),(109,'is_flag','Iceland','Denotes that this entity is associated geographically to the country: Iceland','$vuetify.icons.is_flag',NULL,'2023-06-06 16:53:28','2023-06-06 16:53:28'),(110,'it_flag','Italy','Denotes that this entity is associated geographically to the country: Italy','$vuetify.icons.it_flag',NULL,'2023-06-06 16:53:28','2023-06-06 16:53:28'),(111,'je_flag','Jersey','Denotes that this entity is associated geographically to the country: Jersey','$vuetify.icons.je_flag',NULL,'2023-06-06 16:53:28','2023-06-06 16:53:28'),(112,'jm_flag','Jamaica','Denotes that this entity is associated geographically to the country: Jamaica','$vuetify.icons.jm_flag',NULL,'2023-06-06 16:53:28','2023-06-06 16:53:28'),(113,'jo_flag','Jordan','Denotes that this entity is associated geographically to the country: Jordan','$vuetify.icons.jo_flag',NULL,'2023-06-06 16:53:28','2023-06-06 16:53:28'),(114,'jp_flag','Japan','Denotes that this entity is associated geographically to the country: Japan','$vuetify.icons.jp_flag',NULL,'2023-06-06 16:53:28','2023-06-06 16:53:28'),(115,'ke_flag','Kenya','Denotes that this entity is associated geographically to the country: Kenya','$vuetify.icons.ke_flag',NULL,'2023-06-06 16:53:28','2023-06-06 16:53:28'),(116,'kg_flag','Kyrgyzstan','Denotes that this entity is associated geographically to the country: Kyrgyzstan','$vuetify.icons.kg_flag',NULL,'2023-06-06 16:53:28','2023-06-06 16:53:28'),(117,'kh_flag','Cambodia','Denotes that this entity is associated geographically to the country: Cambodia','$vuetify.icons.kh_flag',NULL,'2023-06-06 16:53:28','2023-06-06 16:53:28'),(118,'ki_flag','Kiribati','Denotes that this entity is associated geographically to the country: Kiribati','$vuetify.icons.ki_flag',NULL,'2023-06-06 16:53:28','2023-06-06 16:53:28'),(119,'km_flag','Comoros','Denotes that this entity is associated geographically to the country: Comoros','$vuetify.icons.km_flag',NULL,'2023-06-06 16:53:28','2023-06-06 16:53:28'),(120,'kn_flag','Saint Kitts and Nevis','Denotes that this entity is associated geographically to the country: Saint Kitts and Nevis','$vuetify.icons.kn_flag',NULL,'2023-06-06 16:53:28','2023-06-06 16:53:28'),(121,'kp_flag','North Korea','Denotes that this entity is associated geographically to the country: North Korea','$vuetify.icons.kp_flag',NULL,'2023-06-06 16:53:28','2023-06-06 16:53:28'),(122,'kr_flag','South Korea','Denotes that this entity is associated geographically to the country: South Korea','$vuetify.icons.kr_flag',NULL,'2023-06-06 16:53:28','2023-06-06 16:53:28'),(123,'kw_flag','Kuwait','Denotes that this entity is associated geographically to the country: Kuwait','$vuetify.icons.kw_flag',NULL,'2023-06-06 16:53:28','2023-06-06 16:53:28'),(124,'ky_flag','Cayman Islands','Denotes that this entity is associated geographically to the country: Cayman Islands','$vuetify.icons.ky_flag',NULL,'2023-06-06 16:53:28','2023-06-06 16:53:28'),(125,'kz_flag','Kazakhstan','Denotes that this entity is associated geographically to the country: Kazakhstan','$vuetify.icons.kz_flag',NULL,'2023-06-06 16:53:28','2023-06-06 16:53:28'),(126,'la_flag','Laos','Denotes that this entity is associated geographically to the country: Laos','$vuetify.icons.la_flag',NULL,'2023-06-06 16:53:28','2023-06-06 16:53:28'),(127,'lb_flag','Lebanon','Denotes that this entity is associated geographically to the country: Lebanon','$vuetify.icons.lb_flag',NULL,'2023-06-06 16:53:28','2023-06-06 16:53:28'),(128,'lc_flag','Saint Lucia','Denotes that this entity is associated geographically to the country: Saint Lucia','$vuetify.icons.lc_flag',NULL,'2023-06-06 16:53:28','2023-06-06 16:53:28'),(129,'li_flag','Liechtenstein','Denotes that this entity is associated geographically to the country: Liechtenstein','$vuetify.icons.li_flag',NULL,'2023-06-06 16:53:28','2023-06-06 16:53:28'),(130,'lk_flag','Sri Lanka','Denotes that this entity is associated geographically to the country: Sri Lanka','$vuetify.icons.lk_flag',NULL,'2023-06-06 16:53:28','2023-06-06 16:53:28'),(131,'lr_flag','Liberia','Denotes that this entity is associated geographically to the country: Liberia','$vuetify.icons.lr_flag',NULL,'2023-06-06 16:53:28','2023-06-06 16:53:28'),(132,'ls_flag','Lesotho','Denotes that this entity is associated geographically to the country: Lesotho','$vuetify.icons.ls_flag',NULL,'2023-06-06 16:53:28','2023-06-06 16:53:28'),(133,'lt_flag','Lithuania','Denotes that this entity is associated geographically to the country: Lithuania','$vuetify.icons.lt_flag',NULL,'2023-06-06 16:53:28','2023-06-06 16:53:28'),(134,'lu_flag','Luxembourg','Denotes that this entity is associated geographically to the country: Luxembourg','$vuetify.icons.lu_flag',NULL,'2023-06-06 16:53:28','2023-06-06 16:53:28'),(135,'lv_flag','Latvia','Denotes that this entity is associated geographically to the country: Latvia','$vuetify.icons.lv_flag',NULL,'2023-06-06 16:53:28','2023-06-06 16:53:28'),(136,'ly_flag','Libya','Denotes that this entity is associated geographically to the country: Libya','$vuetify.icons.ly_flag',NULL,'2023-06-06 16:53:28','2023-06-06 16:53:28'),(137,'ma_flag','Morocco','Denotes that this entity is associated geographically to the country: Morocco','$vuetify.icons.ma_flag',NULL,'2023-06-06 16:53:28','2023-06-06 16:53:28'),(138,'mc_flag','Monaco','Denotes that this entity is associated geographically to the country: Monaco','$vuetify.icons.mc_flag',NULL,'2023-06-06 16:53:28','2023-06-06 16:53:28'),(139,'md_flag','Moldova','Denotes that this entity is associated geographically to the country: Moldova','$vuetify.icons.md_flag',NULL,'2023-06-06 16:53:28','2023-06-06 16:53:28'),(140,'me_flag','Montenegro','Denotes that this entity is associated geographically to the country: Montenegro','$vuetify.icons.me_flag',NULL,'2023-06-06 16:53:28','2023-06-06 16:53:28'),(141,'mf_flag','Saint Martin','Denotes that this entity is associated geographically to the country: Saint Martin','$vuetify.icons.mf_flag',NULL,'2023-06-06 16:53:28','2023-06-06 16:53:28'),(142,'mg_flag','Madagascar','Denotes that this entity is associated geographically to the country: Madagascar','$vuetify.icons.mg_flag',NULL,'2023-06-06 16:53:28','2023-06-06 16:53:28'),(143,'mh_flag','Marshall Islands','Denotes that this entity is associated geographically to the country: Marshall Islands','$vuetify.icons.mh_flag',NULL,'2023-06-06 16:53:28','2023-06-06 16:53:28'),(144,'mk_flag','North Macedonia','Denotes that this entity is associated geographically to the country: North Macedonia','$vuetify.icons.mk_flag',NULL,'2023-06-06 16:53:28','2023-06-06 16:53:28'),(145,'ml_flag','Mali','Denotes that this entity is associated geographically to the country: Mali','$vuetify.icons.ml_flag',NULL,'2023-06-06 16:53:28','2023-06-06 16:53:28'),(146,'mm_flag','Myanmar','Denotes that this entity is associated geographically to the country: Myanmar','$vuetify.icons.mm_flag',NULL,'2023-06-06 16:53:28','2023-06-06 16:53:28'),(147,'mn_flag','Mongolia','Denotes that this entity is associated geographically to the country: Mongolia','$vuetify.icons.mn_flag',NULL,'2023-06-06 16:53:28','2023-06-06 16:53:28'),(148,'mo_flag','Macau','Denotes that this entity is associated geographically to the country: Macau','$vuetify.icons.mo_flag',NULL,'2023-06-06 16:53:28','2023-06-06 16:53:28'),(149,'mp_flag','Northern Mariana Islands','Denotes that this entity is associated geographically to the country: Northern Mariana Islands','$vuetify.icons.mp_flag',NULL,'2023-06-06 16:53:28','2023-06-06 16:53:28'),(150,'mq_flag','Martinique','Denotes that this entity is associated geographically to the country: Martinique','$vuetify.icons.mq_flag',NULL,'2023-06-06 16:53:28','2023-06-06 16:53:28'),(151,'mr_flag','Mauritania','Denotes that this entity is associated geographically to the country: Mauritania','$vuetify.icons.mr_flag',NULL,'2023-06-06 16:53:28','2023-06-06 16:53:28'),(152,'ms_flag','Montserrat','Denotes that this entity is associated geographically to the country: Montserrat','$vuetify.icons.ms_flag',NULL,'2023-06-06 16:53:28','2023-06-06 16:53:28'),(153,'mt_flag','Malta','Denotes that this entity is associated geographically to the country: Malta','$vuetify.icons.mt_flag',NULL,'2023-06-06 16:53:28','2023-06-06 16:53:28'),(154,'mu_flag','Mauritius','Denotes that this entity is associated geographically to the country: Mauritius','$vuetify.icons.mu_flag',NULL,'2023-06-06 16:53:28','2023-06-06 16:53:28'),(155,'mv_flag','Maldives','Denotes that this entity is associated geographically to the country: Maldives','$vuetify.icons.mv_flag',NULL,'2023-06-06 16:53:28','2023-06-06 16:53:28'),(156,'mw_flag','Malawi','Denotes that this entity is associated geographically to the country: Malawi','$vuetify.icons.mw_flag',NULL,'2023-06-06 16:53:28','2023-06-06 16:53:28'),(157,'mx_flag','Mexico','Denotes that this entity is associated geographically to the country: Mexico','$vuetify.icons.mx_flag',NULL,'2023-06-06 16:53:28','2023-06-06 16:53:28'),(158,'my_flag','Malaysia','Denotes that this entity is associated geographically to the country: Malaysia','$vuetify.icons.my_flag',NULL,'2023-06-06 16:53:28','2023-06-06 16:53:28'),(159,'mz_flag','Mozambique','Denotes that this entity is associated geographically to the country: Mozambique','$vuetify.icons.mz_flag',NULL,'2023-06-06 16:53:28','2023-06-06 16:53:28'),(160,'na_flag','Namibia','Denotes that this entity is associated geographically to the country: Namibia','$vuetify.icons.na_flag',NULL,'2023-06-06 16:53:28','2023-06-06 16:53:28'),(161,'nc_flag','New Caledonia','Denotes that this entity is associated geographically to the country: New Caledonia','$vuetify.icons.nc_flag',NULL,'2023-06-06 16:53:28','2023-06-06 16:53:28'),(162,'ne_flag','Niger','Denotes that this entity is associated geographically to the country: Niger','$vuetify.icons.ne_flag',NULL,'2023-06-06 16:53:28','2023-06-06 16:53:28'),(163,'nf_flag','Norfolk Island','Denotes that this entity is associated geographically to the country: Norfolk Island','$vuetify.icons.nf_flag',NULL,'2023-06-06 16:53:28','2023-06-06 16:53:28'),(164,'ng_flag','Nigeria','Denotes that this entity is associated geographically to the country: Nigeria','$vuetify.icons.ng_flag',NULL,'2023-06-06 16:53:28','2023-06-06 16:53:28'),(165,'ni_flag','Nicaragua','Denotes that this entity is associated geographically to the country: Nicaragua','$vuetify.icons.ni_flag',NULL,'2023-06-06 16:53:28','2023-06-06 16:53:28'),(166,'nl_flag','Netherlands','Denotes that this entity is associated geographically to the country: Netherlands','$vuetify.icons.nl_flag',NULL,'2023-06-06 16:53:28','2023-06-06 16:53:28'),(167,'no_flag','Norway','Denotes that this entity is associated geographically to the country: Norway','$vuetify.icons.no_flag',NULL,'2023-06-06 16:53:28','2023-06-06 16:53:28'),(168,'np_flag','Nepal','Denotes that this entity is associated geographically to the country: Nepal','$vuetify.icons.np_flag',NULL,'2023-06-06 16:53:28','2023-06-06 16:53:28'),(169,'nr_flag','Nauru','Denotes that this entity is associated geographically to the country: Nauru','$vuetify.icons.nr_flag',NULL,'2023-06-06 16:53:28','2023-06-06 16:53:28'),(170,'nu_flag','Niue','Denotes that this entity is associated geographically to the country: Niue','$vuetify.icons.nu_flag',NULL,'2023-06-06 16:53:28','2023-06-06 16:53:28'),(171,'nz_flag','New Zealand','Denotes that this entity is associated geographically to the country: New Zealand','$vuetify.icons.nz_flag',NULL,'2023-06-06 16:53:28','2023-06-06 16:53:28'),(172,'om_flag','Oman','Denotes that this entity is associated geographically to the country: Oman','$vuetify.icons.om_flag',NULL,'2023-06-06 16:53:28','2023-06-06 16:53:28'),(173,'pa_flag','Panama','Denotes that this entity is associated geographically to the country: Panama','$vuetify.icons.pa_flag',NULL,'2023-06-06 16:53:28','2023-06-06 16:53:28'),(174,'pe_flag','Peru','Denotes that this entity is associated geographically to the country: Peru','$vuetify.icons.pe_flag',NULL,'2023-06-06 16:53:28','2023-06-06 16:53:28'),(175,'pf_flag','French Polynesia','Denotes that this entity is associated geographically to the country: French Polynesia','$vuetify.icons.pf_flag',NULL,'2023-06-06 16:53:28','2023-06-06 16:53:28'),(176,'pg_flag','Papua New Guinea','Denotes that this entity is associated geographically to the country: Papua New Guinea','$vuetify.icons.pg_flag',NULL,'2023-06-06 16:53:28','2023-06-06 16:53:28'),(177,'ph_flag','Philippines','Denotes that this entity is associated geographically to the country: Philippines','$vuetify.icons.ph_flag',NULL,'2023-06-06 16:53:28','2023-06-06 16:53:28'),(178,'pk_flag','Pakistan','Denotes that this entity is associated geographically to the country: Pakistan','$vuetify.icons.pk_flag',NULL,'2023-06-06 16:53:28','2023-06-06 16:53:28'),(179,'pl_flag','Poland','Denotes that this entity is associated geographically to the country: Poland','$vuetify.icons.pl_flag',NULL,'2023-06-06 16:53:28','2023-06-06 16:53:28'),(180,'pm_flag','Saint Pierre and Miquelon','Denotes that this entity is associated geographically to the country: Saint Pierre and Miquelon','$vuetify.icons.pm_flag',NULL,'2023-06-06 16:53:28','2023-06-06 16:53:28'),(181,'pn_flag','Pitcairn','Denotes that this entity is associated geographically to the country: Pitcairn','$vuetify.icons.pn_flag',NULL,'2023-06-06 16:53:28','2023-06-06 16:53:28'),(182,'pr_flag','Puerto Rico','Denotes that this entity is associated geographically to the country: Puerto Rico','$vuetify.icons.pr_flag',NULL,'2023-06-06 16:53:28','2023-06-06 16:53:28'),(183,'ps_flag','State of Palestine','Denotes that this entity is associated geographically to the country: State of Palestine','$vuetify.icons.ps_flag',NULL,'2023-06-06 16:53:28','2023-06-06 16:53:28'),(184,'pt_flag','Portugal','Denotes that this entity is associated geographically to the country: Portugal','$vuetify.icons.pt_flag',NULL,'2023-06-06 16:53:28','2023-06-06 16:53:28'),(185,'pw_flag','Palau','Denotes that this entity is associated geographically to the country: Palau','$vuetify.icons.pw_flag',NULL,'2023-06-06 16:53:28','2023-06-06 16:53:28'),(186,'py_flag','Paraguay','Denotes that this entity is associated geographically to the country: Paraguay','$vuetify.icons.py_flag',NULL,'2023-06-06 16:53:28','2023-06-06 16:53:28'),(187,'qa_flag','Qatar','Denotes that this entity is associated geographically to the country: Qatar','$vuetify.icons.qa_flag',NULL,'2023-06-06 16:53:28','2023-06-06 16:53:28'),(188,'re_flag','Réunion','Denotes that this entity is associated geographically to the country: Réunion','$vuetify.icons.re_flag',NULL,'2023-06-06 16:53:28','2023-06-06 16:53:28'),(189,'ro_flag','Romania','Denotes that this entity is associated geographically to the country: Romania','$vuetify.icons.ro_flag',NULL,'2023-06-06 16:53:28','2023-06-06 16:53:28'),(190,'rs_flag','Serbia','Denotes that this entity is associated geographically to the country: Serbia','$vuetify.icons.rs_flag',NULL,'2023-06-06 16:53:28','2023-06-06 16:53:28'),(191,'ru_flag','Russia','Denotes that this entity is associated geographically to the country: Russia','$vuetify.icons.ru_flag',NULL,'2023-06-06 16:53:28','2023-06-06 16:53:28'),(192,'rw_flag','Rwanda','Denotes that this entity is associated geographically to the country: Rwanda','$vuetify.icons.rw_flag',NULL,'2023-06-06 16:53:28','2023-06-06 16:53:28'),(193,'sa_flag','Saudi Arabia','Denotes that this entity is associated geographically to the country: Saudi Arabia','$vuetify.icons.sa_flag',NULL,'2023-06-06 16:53:28','2023-06-06 16:53:28'),(194,'sb_flag','Solomon Islands','Denotes that this entity is associated geographically to the country: Solomon Islands','$vuetify.icons.sb_flag',NULL,'2023-06-06 16:53:28','2023-06-06 16:53:28'),(195,'sc_flag','Seychelles','Denotes that this entity is associated geographically to the country: Seychelles','$vuetify.icons.sc_flag',NULL,'2023-06-06 16:53:28','2023-06-06 16:53:28'),(196,'sd_flag','Sudan','Denotes that this entity is associated geographically to the country: Sudan','$vuetify.icons.sd_flag',NULL,'2023-06-06 16:53:28','2023-06-06 16:53:28'),(197,'se_flag','Sweden','Denotes that this entity is associated geographically to the country: Sweden','$vuetify.icons.se_flag',NULL,'2023-06-06 16:53:28','2023-06-06 16:53:28'),(198,'sg_flag','Singapore','Denotes that this entity is associated geographically to the country: Singapore','$vuetify.icons.sg_flag',NULL,'2023-06-06 16:53:28','2023-06-06 16:53:28'),(199,'sh_flag','Saint Helena, Ascension and Tristan da Cunha','Denotes that this entity is associated geographically to the country: Saint Helena, Ascension and Tristan da Cunha','$vuetify.icons.sh_flag',NULL,'2023-06-06 16:53:28','2023-06-06 16:53:28'),(200,'si_flag','Slovenia','Denotes that this entity is associated geographically to the country: Slovenia','$vuetify.icons.si_flag',NULL,'2023-06-06 16:53:28','2023-06-06 16:53:28'),(201,'sj_flag','Svalbard and Jan Mayen','Denotes that this entity is associated geographically to the country: Svalbard and Jan Mayen','$vuetify.icons.sj_flag',NULL,'2023-06-06 16:53:28','2023-06-06 16:53:28'),(202,'sk_flag','Slovakia','Denotes that this entity is associated geographically to the country: Slovakia','$vuetify.icons.sk_flag',NULL,'2023-06-06 16:53:28','2023-06-06 16:53:28'),(203,'sl_flag','Sierra Leone','Denotes that this entity is associated geographically to the country: Sierra Leone','$vuetify.icons.sl_flag',NULL,'2023-06-06 16:53:28','2023-06-06 16:53:28'),(204,'sm_flag','San Marino','Denotes that this entity is associated geographically to the country: San Marino','$vuetify.icons.sm_flag',NULL,'2023-06-06 16:53:28','2023-06-06 16:53:28'),(205,'sn_flag','Senegal','Denotes that this entity is associated geographically to the country: Senegal','$vuetify.icons.sn_flag',NULL,'2023-06-06 16:53:28','2023-06-06 16:53:28'),(206,'so_flag','Somalia','Denotes that this entity is associated geographically to the country: Somalia','$vuetify.icons.so_flag',NULL,'2023-06-06 16:53:28','2023-06-06 16:53:28'),(207,'sr_flag','Suriname','Denotes that this entity is associated geographically to the country: Suriname','$vuetify.icons.sr_flag',NULL,'2023-06-06 16:53:28','2023-06-06 16:53:28'),(208,'ss_flag','South Sudan','Denotes that this entity is associated geographically to the country: South Sudan','$vuetify.icons.ss_flag',NULL,'2023-06-06 16:53:28','2023-06-06 16:53:28'),(209,'st_flag','Sao Tome and Principe','Denotes that this entity is associated geographically to the country: Sao Tome and Principe','$vuetify.icons.st_flag',NULL,'2023-06-06 16:53:28','2023-06-06 16:53:28'),(210,'sv_flag','El Salvador','Denotes that this entity is associated geographically to the country: El Salvador','$vuetify.icons.sv_flag',NULL,'2023-06-06 16:53:28','2023-06-06 16:53:28'),(211,'sx_flag','Sint Maarten','Denotes that this entity is associated geographically to the country: Sint Maarten','$vuetify.icons.sx_flag',NULL,'2023-06-06 16:53:28','2023-06-06 16:53:28'),(212,'sy_flag','Syrian Arab Republic','Denotes that this entity is associated geographically to the country: Syrian Arab Republic','$vuetify.icons.sy_flag',NULL,'2023-06-06 16:53:28','2023-06-06 16:53:28'),(213,'sz_flag','Swaziland','Denotes that this entity is associated geographically to the country: Swaziland','$vuetify.icons.sz_flag',NULL,'2023-06-06 16:53:28','2023-06-06 16:53:28'),(214,'tc_flag','Turks and Caicos Islands','Denotes that this entity is associated geographically to the country: Turks and Caicos Islands','$vuetify.icons.tc_flag',NULL,'2023-06-06 16:53:28','2023-06-06 16:53:28'),(215,'td_flag','Chad','Denotes that this entity is associated geographically to the country: Chad','$vuetify.icons.td_flag',NULL,'2023-06-06 16:53:28','2023-06-06 16:53:28'),(216,'tf_flag','French Southern Territories','Denotes that this entity is associated geographically to the country: French Southern Territories','$vuetify.icons.tf_flag',NULL,'2023-06-06 16:53:28','2023-06-06 16:53:28'),(217,'tg_flag','Togo','Denotes that this entity is associated geographically to the country: Togo','$vuetify.icons.tg_flag',NULL,'2023-06-06 16:53:28','2023-06-06 16:53:28'),(218,'th_flag','Thailand','Denotes that this entity is associated geographically to the country: Thailand','$vuetify.icons.th_flag',NULL,'2023-06-06 16:53:28','2023-06-06 16:53:28'),(219,'tj_flag','Tajikistan','Denotes that this entity is associated geographically to the country: Tajikistan','$vuetify.icons.tj_flag',NULL,'2023-06-06 16:53:28','2023-06-06 16:53:28'),(220,'tk_flag','Tokelau','Denotes that this entity is associated geographically to the country: Tokelau','$vuetify.icons.tk_flag',NULL,'2023-06-06 16:53:28','2023-06-06 16:53:28'),(221,'tl_flag','Timor-Leste','Denotes that this entity is associated geographically to the country: Timor-Leste','$vuetify.icons.tl_flag',NULL,'2023-06-06 16:53:28','2023-06-06 16:53:28'),(222,'tm_flag','Turkmenistan','Denotes that this entity is associated geographically to the country: Turkmenistan','$vuetify.icons.tm_flag',NULL,'2023-06-06 16:53:28','2023-06-06 16:53:28'),(223,'tn_flag','Tunisia','Denotes that this entity is associated geographically to the country: Tunisia','$vuetify.icons.tn_flag',NULL,'2023-06-06 16:53:28','2023-06-06 16:53:28'),(224,'to_flag','Tonga','Denotes that this entity is associated geographically to the country: Tonga','$vuetify.icons.to_flag',NULL,'2023-06-06 16:53:28','2023-06-06 16:53:28'),(225,'tr_flag','Turkey','Denotes that this entity is associated geographically to the country: Turkey','$vuetify.icons.tr_flag',NULL,'2023-06-06 16:53:28','2023-06-06 16:53:28'),(226,'tt_flag','Trinidad and Tobago','Denotes that this entity is associated geographically to the country: Trinidad and Tobago','$vuetify.icons.tt_flag',NULL,'2023-06-06 16:53:28','2023-06-06 16:53:28'),(227,'tv_flag','Tuvalu','Denotes that this entity is associated geographically to the country: Tuvalu','$vuetify.icons.tv_flag',NULL,'2023-06-06 16:53:28','2023-06-06 16:53:28'),(228,'tw_flag','Taiwan','Denotes that this entity is associated geographically to the country: Taiwan','$vuetify.icons.tw_flag',NULL,'2023-06-06 16:53:28','2023-06-06 16:53:28'),(229,'tz_flag','Tanzania','Denotes that this entity is associated geographically to the country: Tanzania','$vuetify.icons.tz_flag',NULL,'2023-06-06 16:53:28','2023-06-06 16:53:28'),(230,'ua_flag','Ukraine','Denotes that this entity is associated geographically to the country: Ukraine','$vuetify.icons.ua_flag',NULL,'2023-06-06 16:53:28','2023-06-06 16:53:28'),(231,'ug_flag','Uganda','Denotes that this entity is associated geographically to the country: Uganda','$vuetify.icons.ug_flag',NULL,'2023-06-06 16:53:28','2023-06-06 16:53:28'),(232,'um_flag','United States Minor Outlying Islands','Denotes that this entity is associated geographically to the country: United States Minor Outlying Islands','$vuetify.icons.um_flag',NULL,'2023-06-06 16:53:28','2023-06-06 16:53:28'),(233,'us_flag','United States of America','Denotes that this entity is associated geographically to the country: United States of America','$vuetify.icons.us_flag',NULL,'2023-06-06 16:53:28','2023-06-06 16:53:28'),(234,'uy_flag','Uruguay','Denotes that this entity is associated geographically to the country: Uruguay','$vuetify.icons.uy_flag',NULL,'2023-06-06 16:53:28','2023-06-06 16:53:28'),(235,'uz_flag','Uzbekistan','Denotes that this entity is associated geographically to the country: Uzbekistan','$vuetify.icons.uz_flag',NULL,'2023-06-06 16:53:28','2023-06-06 16:53:28'),(236,'va_flag','Holy See','Denotes that this entity is associated geographically to the country: Holy See','$vuetify.icons.va_flag',NULL,'2023-06-06 16:53:28','2023-06-06 16:53:28'),(237,'vc_flag','Saint Vincent and the Grenadines','Denotes that this entity is associated geographically to the country: Saint Vincent and the Grenadines','$vuetify.icons.vc_flag',NULL,'2023-06-06 16:53:28','2023-06-06 16:53:28'),(238,'ve_flag','Venezuela (Bolivarian Republic of)','Denotes that this entity is associated geographically to the country: Venezuela (Bolivarian Republic of)','$vuetify.icons.ve_flag',NULL,'2023-06-06 16:53:28','2023-06-06 16:53:28'),(239,'vg_flag','Virgin Islands (British)','Denotes that this entity is associated geographically to the country: Virgin Islands (British)','$vuetify.icons.vg_flag',NULL,'2023-06-06 16:53:28','2023-06-06 16:53:28'),(240,'vi_flag','Virgin Islands (U.S.)','Denotes that this entity is associated geographically to the country: Virgin Islands (U.S.)','$vuetify.icons.vi_flag',NULL,'2023-06-06 16:53:28','2023-06-06 16:53:28'),(241,'vn_flag','Vietnam','Denotes that this entity is associated geographically to the country: Vietnam','$vuetify.icons.vn_flag',NULL,'2023-06-06 16:53:28','2023-06-06 16:53:28'),(242,'vu_flag','Vanuatu','Denotes that this entity is associated geographically to the country: Vanuatu','$vuetify.icons.vu_flag',NULL,'2023-06-06 16:53:28','2023-06-06 16:53:28'),(243,'wf_flag','Wallis and Futuna','Denotes that this entity is associated geographically to the country: Wallis and Futuna','$vuetify.icons.wf_flag',NULL,'2023-06-06 16:53:28','2023-06-06 16:53:28'),(244,'ws_flag','Samoa','Denotes that this entity is associated geographically to the country: Samoa','$vuetify.icons.ws_flag',NULL,'2023-06-06 16:53:28','2023-06-06 16:53:28'),(245,'ye_flag','Yemen','Denotes that this entity is associated geographically to the country: Yemen','$vuetify.icons.ye_flag',NULL,'2023-06-06 16:53:28','2023-06-06 16:53:28'),(246,'yt_flag','Mayotte','Denotes that this entity is associated geographically to the country: Mayotte','$vuetify.icons.yt_flag',NULL,'2023-06-06 16:53:28','2023-06-06 16:53:28'),(247,'za_flag','South Africa','Denotes that this entity is associated geographically to the country: South Africa','$vuetify.icons.za_flag',NULL,'2023-06-06 16:53:28','2023-06-06 16:53:28'),(248,'zm_flag','Zambia','Denotes that this entity is associated geographically to the country: Zambia','$vuetify.icons.zm_flag',NULL,'2023-06-06 16:53:28','2023-06-06 16:53:28'),(249,'zw_flag','Zimbabwe','Denotes that this entity is associated geographically to the country: Zimbabwe','$vuetify.icons.zw_flag',NULL,'2023-06-06 16:53:28','2023-06-06 16:53:28'),(250,'scanner','Scanner','This entity class is usually applied to an external IP address that is known or suspected to be guilty of scanning infrastructure.','$vuetify.icons.scanner',NULL,'2023-06-06 16:53:28','2023-06-06 16:53:28'),(251,'sandia','Sandia National Labs','This entity class is applied to entities beloning to Sandia National Labs.','$vuetify.icons.sandia_thunderbird',NULL,'2023-06-06 16:53:28','2023-06-06 16:53:28'),(252,'firewall','Firewall Block','This entity class is usually applied to an external IP address that has been blocked by ingress firewalls.','$vuetify.icons.firewall',NULL,'2023-06-06 16:53:28','2023-06-06 16:53:28'),(253,'anonymous_ip','Anonymous IP','This entity class is usually applied to an external IP address that has been labeled as an anonymous ip address.','$vuetify.icons.anonymous_ip',NULL,'2023-06-06 16:53:28','2023-06-06 16:53:28'),(254,'anonymous_vpn','Anonymous VPN','This entity class is usually applied to an external IP address that has been labeled as known VPN exit node.','mdi-vpn',NULL,'2023-06-06 16:53:28','2023-06-06 16:53:28'),(255,'hosting_provider','Hosting Provider','This entity class is usually applied to an external IP address that has been labeled as belonging to a known hosting provider.','mdi-satellite-uplink',NULL,'2023-06-06 16:53:28','2023-06-06 16:53:28'),(256,'public_proxy','Public Proxy','This entity class is usually applied to an external IP address that has been labeled as belonging to a public proxy.','mdi-cloud-arrow-down-outline',NULL,'2023-06-06 16:53:28','2023-06-06 16:53:28'),(257,'tor_exit_node','Tor Node','This entity class is usually applied to an external IP address that has been labeled as belonging to a tor exit node.','mdi-vector-triangle',NULL,'2023-06-06 16:53:28','2023-06-06 16:53:28'),(258,'blackhole','DNS Blackhole','This entity class is usually applied to an external IP  that has been blackholed by our DNS resolvers.','mdi-pi-hole',NULL,'2023-06-06 16:53:28','2023-06-06 16:53:28'),(259,'proxyblock','Proxy Block','This entity class is usually applied to an external IP that has been blocked by our forward proxies.','mdi-cancel',NULL,'2023-06-06 16:53:28','2023-06-06 16:53:28'),(260,'watchlist','Watchlist','This entity class is usually applied to an external IP that has been added to our threat intel watchlists.','mdi-binoculars',NULL,'2023-06-06 16:53:28','2023-06-06 16:53:28'),(261,'whitelist','Allow List','This entity class is usually applied to an external IP that has been added to our ingress firewall allow lists.','mdi-human-greeting',NULL,'2023-06-06 16:53:28','2023-06-06 16:53:28'),(262,'user_principal','Azure AD User Principal','This entity class is applied to a user principal identity from Active Directory. Entity accounts are technically considered user principals in Active Directory, but are not labeled with this entity class for clarity\'s sake.','mdi-account-check',NULL,'2023-06-06 16:53:28','2023-06-06 16:53:28'),(263,'email_alias','Email Alias','This entity class is applied to an SMTP alias for a user principal in Active Directory. NOTE that entity accounts are considered user principals.','mdi-card-account-mail-outline',NULL,'2023-06-06 16:53:28','2023-06-06 16:53:28'),(264,'entity_account','Entity Account','This entity class is applied to a user in active directory listed as an \'entity account\' or non-human user.','mdi-robot',NULL,'2023-06-06 16:53:28','2023-06-06 16:53:28');
/*!40000 ALTER TABLE `entity_classes` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `entity_types`
--

DROP TABLE IF EXISTS `entity_types`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `entity_types` (
  `entity_type_id` int NOT NULL AUTO_INCREMENT,
  `entity_type_name` varchar(300) DEFAULT NULL,
  `match_order` int DEFAULT NULL,
  `status` enum('active','disabled') NOT NULL,
  `options` json DEFAULT NULL,
  `match` text,
  `entity_type_data_ver` text,
  `entity_type_data` json DEFAULT NULL,
  `created_date` datetime DEFAULT NULL,
  `modified_date` datetime NOT NULL,
  PRIMARY KEY (`entity_type_id`),
  UNIQUE KEY `entity_type_name` (`entity_type_name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `entity_types`
--

LOCK TABLES `entity_types` WRITE;
/*!40000 ALTER TABLE `entity_types` DISABLE KEYS */;
/*!40000 ALTER TABLE `entity_types` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `entries`
--

DROP TABLE IF EXISTS `entries`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `entries` (
  `entry_id` int NOT NULL AUTO_INCREMENT,
  `owner` text NOT NULL,
  `tlp` enum('unset','white','green','amber','red','black','clear','amber_strict') NOT NULL,
  `parent_entry_id` int DEFAULT NULL,
  `target_type` enum('alert','alertgroup','checklist','dispatch','entity','entry','event','file','guide','incident','intel','product','sigbody','signature','entity_class','entity_type','source','stat','tag','admin','threat_model_item','feed','pivot','none','vuln_feed','vuln_track') NOT NULL,
  `target_id` int NOT NULL,
  `entryclass` enum('entry','summary','task','promotion','action') DEFAULT NULL,
  `entry_data_ver` text,
  `entry_data` json DEFAULT NULL,
  `parsed` tinyint(1) NOT NULL,
  `created_date` datetime DEFAULT NULL,
  `modified_date` datetime NOT NULL,
  PRIMARY KEY (`entry_id`),
  KEY `parent_entry_id` (`parent_entry_id`),
  KEY `entry_speedup` (`target_type`,`target_id`),
  CONSTRAINT `entries_ibfk_1` FOREIGN KEY (`parent_entry_id`) REFERENCES `entries` (`entry_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `entries`
--

LOCK TABLES `entries` WRITE;
/*!40000 ALTER TABLE `entries` DISABLE KEYS */;
/*!40000 ALTER TABLE `entries` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `events`
--

DROP TABLE IF EXISTS `events`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `events` (
  `event_id` int NOT NULL AUTO_INCREMENT,
  `owner` text NOT NULL,
  `tlp` enum('unset','white','green','amber','red','black','clear','amber_strict') NOT NULL,
  `status` enum('open','promoted','closed') DEFAULT NULL,
  `subject` text,
  `view_count` int NOT NULL,
  `message_id` text,
  `created_date` datetime DEFAULT NULL,
  `modified_date` datetime NOT NULL,
  PRIMARY KEY (`event_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `events`
--

LOCK TABLES `events` WRITE;
/*!40000 ALTER TABLE `events` DISABLE KEYS */;
/*!40000 ALTER TABLE `events` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `feed_types`
--

DROP TABLE IF EXISTS `feed_types`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `feed_types` (
  `feed_type` varchar(255) NOT NULL,
  `created_date` datetime DEFAULT NULL,
  `modified_date` datetime NOT NULL,
  PRIMARY KEY (`feed_type`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `feed_types`
--

LOCK TABLES `feed_types` WRITE;
/*!40000 ALTER TABLE `feed_types` DISABLE KEYS */;
/*!40000 ALTER TABLE `feed_types` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `feeds`
--

DROP TABLE IF EXISTS `feeds`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `feeds` (
  `feed_id` int NOT NULL AUTO_INCREMENT,
  `feed_name` text NOT NULL,
  `owner` text NOT NULL,
  `tlp` enum('unset','white','green','amber','red','black','clear','amber_strict') NOT NULL,
  `status` text NOT NULL,
  `feed_type` text NOT NULL,
  `uri` text NOT NULL,
  `article_count` int NOT NULL,
  `promotions_count` int NOT NULL,
  `last_article` datetime DEFAULT NULL,
  `last_attempt` datetime DEFAULT NULL,
  `feed_data` json DEFAULT NULL,
  `created_date` datetime DEFAULT NULL,
  `modified_date` datetime NOT NULL,
  PRIMARY KEY (`feed_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `feeds`
--

LOCK TABLES `feeds` WRITE;
/*!40000 ALTER TABLE `feeds` DISABLE KEYS */;
/*!40000 ALTER TABLE `feeds` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `files`
--

DROP TABLE IF EXISTS `files`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `files` (
  `file_id` int NOT NULL AUTO_INCREMENT,
  `file_pointer` varchar(70) NOT NULL,
  `owner` text NOT NULL,
  `tlp` enum('unset','white','green','amber','red','black','clear','amber_strict') NOT NULL,
  `filename` text,
  `filesize` int DEFAULT NULL,
  `sha256` text,
  `description` text,
  `content_type` text,
  `created_date` datetime DEFAULT NULL,
  `modified_date` datetime NOT NULL,
  PRIMARY KEY (`file_id`),
  UNIQUE KEY `file_pointer` (`file_pointer`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `files`
--

LOCK TABLES `files` WRITE;
/*!40000 ALTER TABLE `files` DISABLE KEYS */;
/*!40000 ALTER TABLE `files` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `games`
--

DROP TABLE IF EXISTS `games`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `games` (
  `game_id` int NOT NULL AUTO_INCREMENT,
  `game_name` text,
  `tooltip` text,
  `results` json DEFAULT NULL,
  `created_date` datetime DEFAULT NULL,
  `modified_date` datetime NOT NULL,
  PRIMARY KEY (`game_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `games`
--

LOCK TABLES `games` WRITE;
/*!40000 ALTER TABLE `games` DISABLE KEYS */;
/*!40000 ALTER TABLE `games` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `guides`
--

DROP TABLE IF EXISTS `guides`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `guides` (
  `guide_id` int NOT NULL AUTO_INCREMENT,
  `owner` text NOT NULL,
  `tlp` enum('unset','white','green','amber','red','black','clear','amber_strict') NOT NULL,
  `subject` text,
  `status` enum('current','outdated') NOT NULL,
  `application` json DEFAULT NULL,
  `guide_data_ver` text,
  `guide_data` json DEFAULT NULL,
  `created_date` datetime DEFAULT NULL,
  `modified_date` datetime NOT NULL,
  PRIMARY KEY (`guide_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `guides`
--

LOCK TABLES `guides` WRITE;
/*!40000 ALTER TABLE `guides` DISABLE KEYS */;
/*!40000 ALTER TABLE `guides` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `handlers`
--

DROP TABLE IF EXISTS `handlers`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `handlers` (
  `handler_id` int NOT NULL AUTO_INCREMENT,
  `start_date` datetime NOT NULL,
  `end_date` datetime NOT NULL,
  `username` text NOT NULL,
  `position` text,
  `created_date` datetime DEFAULT NULL,
  `modified_date` datetime NOT NULL,
  PRIMARY KEY (`handler_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `handlers`
--

LOCK TABLES `handlers` WRITE;
/*!40000 ALTER TABLE `handlers` DISABLE KEYS */;
/*!40000 ALTER TABLE `handlers` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `incidents`
--

DROP TABLE IF EXISTS `incidents`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `incidents` (
  `incident_id` int NOT NULL AUTO_INCREMENT,
  `owner` text NOT NULL,
  `tlp` enum('unset','white','green','amber','red','black','clear','amber_strict') NOT NULL,
  `occurred_date` datetime DEFAULT NULL,
  `discovered_date` datetime DEFAULT NULL,
  `reported_date` datetime DEFAULT NULL,
  `status` enum('open','promoted','closed') DEFAULT NULL,
  `subject` text,
  `incident_data_ver` text,
  `incident_data` json DEFAULT NULL,
  `view_count` int NOT NULL,
  `created_date` datetime DEFAULT NULL,
  `modified_date` datetime NOT NULL,
  PRIMARY KEY (`incident_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `incidents`
--

LOCK TABLES `incidents` WRITE;
/*!40000 ALTER TABLE `incidents` DISABLE KEYS */;
/*!40000 ALTER TABLE `incidents` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `intels`
--

DROP TABLE IF EXISTS `intels`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `intels` (
  `intel_id` int NOT NULL AUTO_INCREMENT,
  `owner` text NOT NULL,
  `tlp` enum('unset','white','green','amber','red','black','clear','amber_strict') NOT NULL,
  `subject` text,
  `status` enum('open','promoted','closed') DEFAULT NULL,
  `created_date` datetime DEFAULT NULL,
  `modified_date` datetime NOT NULL,
  PRIMARY KEY (`intel_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `intels`
--

LOCK TABLES `intels` WRITE;
/*!40000 ALTER TABLE `intels` DISABLE KEYS */;
/*!40000 ALTER TABLE `intels` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `links`
--

DROP TABLE IF EXISTS `links`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `links` (
  `link_id` int NOT NULL AUTO_INCREMENT,
  `v0_type` enum('alert','alertgroup','checklist','dispatch','entity','entry','event','file','guide','incident','intel','product','sigbody','signature','entity_class','entity_type','source','stat','tag','admin','threat_model_item','feed','pivot','none','vuln_feed','vuln_track') NOT NULL,
  `v0_id` int NOT NULL,
  `v1_type` enum('alert','alertgroup','checklist','dispatch','entity','entry','event','file','guide','incident','intel','product','sigbody','signature','entity_class','entity_type','source','stat','tag','admin','threat_model_item','feed','pivot','none','vuln_feed','vuln_track') NOT NULL,
  `v1_id` int NOT NULL,
  `weight` int DEFAULT NULL,
  `context` text,
  `created_date` datetime DEFAULT NULL,
  `modified_date` datetime NOT NULL,
  PRIMARY KEY (`link_id`),
  KEY `link_speedup` (`v0_id`,`v1_type`,`v0_type`),
  KEY `link_speedup_2` (`v1_id`,`v0_type`,`v1_type`),
  KEY `link_speedup_3` (`v0_type`,`v0_id`),
  KEY `link_speedup_4` (`v1_type`,`v1_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `links`
--

LOCK TABLES `links` WRITE;
/*!40000 ALTER TABLE `links` DISABLE KEYS */;
/*!40000 ALTER TABLE `links` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `metrics`
--

DROP TABLE IF EXISTS `metrics`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4*/;
CREATE TABLE `metrics` (
  `metric_id` int NOT NULL AUTO_INCREMENT,
  `metric_name` text COLLATE utf8mb4_unicode_ci,
  `tooltip` text COLLATE utf8mb4_unicode_ci,
  `results` json DEFAULT NULL,
  `created_date` datetime DEFAULT NULL,
  `modified_date` datetime NOT NULL,
  PRIMARY KEY (`metric_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `notifications`
--

DROP TABLE IF EXISTS `notifications`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `notifications` (
  `notification_id` int NOT NULL AUTO_INCREMENT,
  `user_id` int DEFAULT NULL,
  `notification_message` text NOT NULL,
  `notification_ack` tinyint(1) NOT NULL,
  `ref_id` text,
  `created_date` datetime DEFAULT NULL,
  `modified_date` datetime NOT NULL,
  PRIMARY KEY (`notification_id`),
  KEY `user_id` (`user_id`),
  CONSTRAINT `notifications_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `notifications`
--

LOCK TABLES `notifications` WRITE;
/*!40000 ALTER TABLE `notifications` DISABLE KEYS */;
/*!40000 ALTER TABLE `notifications` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `object_permissions`
--

DROP TABLE IF EXISTS `object_permissions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `object_permissions` (
  `object_permission_id` int NOT NULL AUTO_INCREMENT,
  `role_id` int DEFAULT NULL,
  `target_type` enum('alert','alertgroup','checklist','dispatch','entity','entry','event','file','guide','incident','intel','product','sigbody','signature','entity_class','entity_type','source','stat','tag','admin','threat_model_item','feed','pivot','none','vuln_feed','vuln_track') NOT NULL,
  `target_id` int NOT NULL,
  `permission` enum('read','modify','delete','admin') NOT NULL,
  PRIMARY KEY (`object_permission_id`),
  KEY `ix_object_permissions_object_permission_id` (`object_permission_id`),
  KEY `permission_speedup_1` (`target_id`,`target_type`,`permission`,`role_id`),
  KEY `permission_speedup_2` (`permission`,`target_type`,`role_id`,`target_id`),
  KEY `permission_speedup_3` (`target_type`,`role_id`),
  KEY `permission_role_index` (`role_id`),
  CONSTRAINT `object_permissions_ibfk_1` FOREIGN KEY (`role_id`) REFERENCES `roles` (`role_id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `object_permissions`
--

LOCK TABLES `object_permissions` WRITE;
/*!40000 ALTER TABLE `object_permissions` DISABLE KEYS */;
INSERT INTO `object_permissions` VALUES (1,2,'admin',0,'admin');
/*!40000 ALTER TABLE `object_permissions` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `pivots`
--

DROP TABLE IF EXISTS `pivots`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `pivots` (
  `pivot_id` int NOT NULL AUTO_INCREMENT,
  `pivot_template` text NOT NULL,
  `pivot_title` text NOT NULL,
  `pivot_description` text,
  `created_date` datetime DEFAULT NULL,
  `modified_date` datetime NOT NULL,
  PRIMARY KEY (`pivot_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `pivots`
--

LOCK TABLES `pivots` WRITE;
/*!40000 ALTER TABLE `pivots` DISABLE KEYS */;
/*!40000 ALTER TABLE `pivots` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `pivots_entity_classes`
--

DROP TABLE IF EXISTS `pivots_entity_classes`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `pivots_entity_classes` (
  `pivot_id` int NOT NULL,
  `entity_class_id` int NOT NULL,
  PRIMARY KEY (`pivot_id`,`entity_class_id`),
  KEY `entity_class_id` (`entity_class_id`),
  CONSTRAINT `pivots_entity_classes_ibfk_1` FOREIGN KEY (`pivot_id`) REFERENCES `pivots` (`pivot_id`),
  CONSTRAINT `pivots_entity_classes_ibfk_2` FOREIGN KEY (`entity_class_id`) REFERENCES `entity_classes` (`entity_class_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `pivots_entity_classes`
--

LOCK TABLES `pivots_entity_classes` WRITE;
/*!40000 ALTER TABLE `pivots_entity_classes` DISABLE KEYS */;
/*!40000 ALTER TABLE `pivots_entity_classes` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `pivots_entity_types`
--

DROP TABLE IF EXISTS `pivots_entity_types`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `pivots_entity_types` (
  `pivot_id` int NOT NULL,
  `entity_type_id` int NOT NULL,
  PRIMARY KEY (`pivot_id`,`entity_type_id`),
  KEY `entity_type_id` (`entity_type_id`),
  CONSTRAINT `pivots_entity_types_ibfk_1` FOREIGN KEY (`pivot_id`) REFERENCES `pivots` (`pivot_id`),
  CONSTRAINT `pivots_entity_types_ibfk_2` FOREIGN KEY (`entity_type_id`) REFERENCES `entity_types` (`entity_type_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `pivots_entity_types`
--

LOCK TABLES `pivots_entity_types` WRITE;
/*!40000 ALTER TABLE `pivots_entity_types` DISABLE KEYS */;
/*!40000 ALTER TABLE `pivots_entity_types` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `products`
--

DROP TABLE IF EXISTS `products`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `products` (
  `products_id` int NOT NULL AUTO_INCREMENT,
  `owner` text NOT NULL,
  `tlp` enum('unset','white','green','amber','red','black','clear','amber_strict') NOT NULL,
  `subject` text,
  `created_date` datetime DEFAULT NULL,
  `modified_date` datetime NOT NULL,
  PRIMARY KEY (`products_id`),
  KEY `ix_products_products_id` (`products_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `products`
--

LOCK TABLES `products` WRITE;
/*!40000 ALTER TABLE `products` DISABLE KEYS */;
/*!40000 ALTER TABLE `products` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `promotions`
--

DROP TABLE IF EXISTS `promotions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `promotions` (
  `promotion_id` int NOT NULL AUTO_INCREMENT,
  `p0_id` int NOT NULL,
  `p0_type` enum('alert','alertgroup','checklist','dispatch','entity','entry','event','file','guide','incident','intel','product','sigbody','signature','entity_class','entity_type','source','stat','tag','admin','threat_model_item','feed','pivot','none','vuln_feed','vuln_track') NOT NULL,
  `p1_id` int NOT NULL,
  `p1_type` enum('alert','alertgroup','checklist','dispatch','entity','entry','event','file','guide','incident','intel','product','sigbody','signature','entity_class','entity_type','source','stat','tag','admin','threat_model_item','feed','pivot','none','vuln_feed','vuln_track') NOT NULL,
  `created_date` datetime DEFAULT NULL,
  `modified_date` datetime NOT NULL,
  PRIMARY KEY (`promotion_id`),
  KEY `promotion_speedup_1` (`p0_id`,`p0_type`),
  KEY `promotion_speedup_2` (`p1_id`,`p1_type`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `promotions`
--

LOCK TABLES `promotions` WRITE;
/*!40000 ALTER TABLE `promotions` DISABLE KEYS */;
/*!40000 ALTER TABLE `promotions` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structire for table `remote_flairs`
--

DROP TABLE IF EXISTS `remote_flairs`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `remote_flairs` (
  `id` int NOT NULL AUTO_INCREMENT,
  `md5` varchar(32) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `uri` text COLLATE utf8mb4_unicode_ci,
  `status` enum('requested','processing','ready','error','reflair') COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `results` json DEFAULT NULL,
  `created_date` datetime DEFAULT NULL,
  `modified_date` datetime NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `md5` (`md5`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `roles`
--

DROP TABLE IF EXISTS `roles`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `roles` (
  `role_id` int NOT NULL AUTO_INCREMENT,
  `role_name` varchar(255) NOT NULL,
  `description` text,
  `created_date` datetime DEFAULT NULL,
  `modified_date` datetime NOT NULL,
  PRIMARY KEY (`role_id`),
  UNIQUE KEY `role_name` (`role_name`),
  KEY `ix_roles_role_id` (`role_id`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `roles`
--

LOCK TABLES `roles` WRITE;
/*!40000 ALTER TABLE `roles` DISABLE KEYS */;
INSERT INTO `roles` VALUES (1,'everyone',NULL,'2023-06-06 16:53:27','2023-06-06 16:53:27'),(2,'admin',NULL,'2023-06-06 16:53:27','2023-06-06 16:53:27');
/*!40000 ALTER TABLE `roles` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `roles_auth`
--

DROP TABLE IF EXISTS `roles_auth`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `roles_auth` (
  `role_id` int DEFAULT NULL,
  `settings_id` int DEFAULT NULL,
  KEY `role_id` (`role_id`),
  KEY `settings_id` (`settings_id`),
  CONSTRAINT `roles_auth_ibfk_1` FOREIGN KEY (`role_id`) REFERENCES `roles` (`role_id`),
  CONSTRAINT `roles_auth_ibfk_2` FOREIGN KEY (`settings_id`) REFERENCES `auth_settings` (`auth_settings_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `roles_auth`
--

LOCK TABLES `roles_auth` WRITE;
/*!40000 ALTER TABLE `roles_auth` DISABLE KEYS */;
/*!40000 ALTER TABLE `roles_auth` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `settings`
--

DROP TABLE IF EXISTS `settings`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `settings` (
  `settings_id` int NOT NULL AUTO_INCREMENT,
  `site_name` text COLLATE utf8mb4_unicode_ci,
  `env_level` text COLLATE utf8mb4_unicode_ci,
  `it_contact` text COLLATE utf8mb4_unicode_ci,
  `time_zone` text COLLATE utf8mb4_unicode_ci,
  `default_permissions` json DEFAULT NULL,
  `created_date` datetime DEFAULT NULL,
  `modified_date` datetime NOT NULL,
  PRIMARY KEY (`settings_id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `settings`
--

LOCK TABLES `settings` WRITE;
/*!40000 ALTER TABLE `settings` DISABLE KEYS */;
INSERT INTO `settings` VALUES (1,'','','scot-admin@example.com','',NULL,'2023-06-06 16:53:27','2023-06-06 16:53:27');
/*!40000 ALTER TABLE `settings` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `sigbodies`
--

DROP TABLE IF EXISTS `sigbodies`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `sigbodies` (
  `sigbody_id` int NOT NULL AUTO_INCREMENT,
  `revision` int DEFAULT NULL,
  `body` text,
  `body64` text,
  `signature_id` int DEFAULT NULL,
  `created_date` datetime DEFAULT NULL,
  `modified_date` datetime NOT NULL,
  PRIMARY KEY (`sigbody_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `sigbodies`
--

LOCK TABLES `sigbodies` WRITE;
/*!40000 ALTER TABLE `sigbodies` DISABLE KEYS */;
/*!40000 ALTER TABLE `sigbodies` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `signatures`
--

DROP TABLE IF EXISTS `signatures`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `signatures` (
  `signature_id` int NOT NULL AUTO_INCREMENT,
  `owner` text NOT NULL,
  `tlp_enum` enum('unset','white','green','amber','red','black','clear','amber_strict') NOT NULL,
  `latest_revision` int DEFAULT NULL,
  `signature_name` text,
  `signature_description` text,
  `signature_type` text,
  `status` text,
  `stats` json DEFAULT NULL,
  `options` json DEFAULT NULL,
  `signature_data_ver` text,
  `signature_data` json DEFAULT NULL,
  `created_date` datetime DEFAULT NULL,
  `modified_date` datetime NOT NULL,
  PRIMARY KEY (`signature_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `signatures`
--

LOCK TABLES `signatures` WRITE;
/*!40000 ALTER TABLE `signatures` DISABLE KEYS */;
/*!40000 ALTER TABLE `signatures` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `sources`
--

DROP TABLE IF EXISTS `sources`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `sources` (
  `source_id` int NOT NULL AUTO_INCREMENT,
  `source_name` varchar(300) NOT NULL,
  `description` text,
  `created_date` datetime DEFAULT NULL,
  `modified_date` datetime NOT NULL,
  PRIMARY KEY (`source_id`),
  UNIQUE KEY `source_name` (`source_name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `sources`
--

LOCK TABLES `sources` WRITE;
/*!40000 ALTER TABLE `sources` DISABLE KEYS */;
/*!40000 ALTER TABLE `sources` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `stats`
--

DROP TABLE IF EXISTS `stats`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `stats` (
  `stat_id` int NOT NULL AUTO_INCREMENT,
  `stat_year` int NOT NULL,
  `stat_quarter` int NOT NULL,
  `stat_month` int NOT NULL,
  `stat_day_of_week` int NOT NULL,
  `stat_day` int NOT NULL,
  `stat_hour` int NOT NULL,
  `stat_metric` text NOT NULL,
  `stat_value` int NOT NULL,
  PRIMARY KEY (`stat_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `stats`
--

LOCK TABLES `stats` WRITE;
/*!40000 ALTER TABLE `stats` DISABLE KEYS */;
/*!40000 ALTER TABLE `stats` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `storage_settings`
--

DROP TABLE IF EXISTS `storage_settings`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `storage_settings` (
  `storage_settings_id` int NOT NULL AUTO_INCREMENT,
  `storage_provider_name` text,
  `storage_provider` enum('s3','emc','disk') DEFAULT NULL,
  `storage_config` json DEFAULT NULL,
  `enabled` tinyint(1) DEFAULT NULL,
  `created_date` datetime DEFAULT NULL,
  `modified_date` datetime NOT NULL,
  PRIMARY KEY (`storage_settings_id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `storage_settings`
--

LOCK TABLES `storage_settings` WRITE;
/*!40000 ALTER TABLE `storage_settings` DISABLE KEYS */;
INSERT INTO `storage_settings` VALUES (1,NULL,'disk','{\"provider_name\": \"Local File System\", \"root_directory\": \"/var/scot_files\", \"deleted_items_directory\": \"/var/scot_files/_deleted_items\"}',1,'2023-06-06 16:53:27','2023-06-06 16:53:27');
/*!40000 ALTER TABLE `storage_settings` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `tag_types`
--

DROP TABLE IF EXISTS `tag_types`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `tag_types` (
  `tag_type_id` int NOT NULL AUTO_INCREMENT,
  `tag_type_name` text NOT NULL,
  `description` text,
  `created_date` datetime DEFAULT NULL,
  `modified_date` datetime NOT NULL,
  PRIMARY KEY (`tag_type_id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `tag_types`
--

LOCK TABLES `tag_types` WRITE;
/*!40000 ALTER TABLE `tag_types` DISABLE KEYS */;
INSERT INTO `tag_types` VALUES (1,'General','Generic/Default Tag Type','2023-06-06 16:53:27','2023-06-06 16:53:27');
/*!40000 ALTER TABLE `tag_types` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `tags`
--

DROP TABLE IF EXISTS `tags`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `tags` (
  `tag_id` int NOT NULL AUTO_INCREMENT,
  `tag_name` text NOT NULL,
  `description` text,
  `tag_type_id` int DEFAULT NULL,
  `created_date` datetime DEFAULT NULL,
  `modified_date` datetime NOT NULL,
  PRIMARY KEY (`tag_id`),
  KEY `tag_type_id` (`tag_type_id`),
  CONSTRAINT `tags_ibfk_1` FOREIGN KEY (`tag_type_id`) REFERENCES `tag_types` (`tag_type_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `tags`
--

LOCK TABLES `tags` WRITE;
/*!40000 ALTER TABLE `tags` DISABLE KEYS */;
/*!40000 ALTER TABLE `tags` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `threat_model_items`
--

DROP TABLE IF EXISTS `threat_model_items`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `threat_model_items` (
  `threat_model_id` int NOT NULL AUTO_INCREMENT,
  `title` varchar(512) DEFAULT NULL,
  `description` text,
  `threat_model_type` text,
  `threat_model_data` json DEFAULT NULL,
  `created_date` datetime DEFAULT NULL,
  `modified_date` datetime NOT NULL,
  PRIMARY KEY (`threat_model_id`),
  KEY `ix_threat_model_items_threat_model_id` (`threat_model_id`),
  KEY `ix_threat_model_items_title` (`title`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `threat_model_items`
--

LOCK TABLES `threat_model_items` WRITE;
/*!40000 ALTER TABLE `threat_model_items` DISABLE KEYS */;
/*!40000 ALTER TABLE `threat_model_items` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `users`
--

DROP TABLE IF EXISTS `users`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `users` (
  `user_id` int NOT NULL AUTO_INCREMENT,
  `username` varchar(255) NOT NULL,
  `last_login_date` datetime DEFAULT NULL,
  `last_activity_date` datetime DEFAULT NULL,
  `failed_attempt_count` smallint DEFAULT NULL,
  `is_active` tinyint(1) DEFAULT NULL,
  `pwhash` text,
  `fullname` text,
  `email` varchar(255) DEFAULT NULL,
  `preferences` json DEFAULT NULL,
  `is_superuser` tinyint(1) DEFAULT NULL,
  `created_date` datetime DEFAULT NULL,
  `modified_date` datetime NOT NULL,
  PRIMARY KEY (`user_id`),
  UNIQUE KEY `username` (`username`),
  KEY `ix_users_email` (`email`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `users`
--

LOCK TABLES `users` WRITE;
/*!40000 ALTER TABLE `users` DISABLE KEYS */;
INSERT INTO `users` VALUES (1,'scot-admin','2023-06-06 16:53:27','2023-06-06 16:53:27',0,1,'$2b$12$bW05CH368VHMy5VTmiV/Du897N1JqGM9HaqMkfmy163zn3EId/Snm','SCOT-ADMIN','scot-admin@example.com',NULL,1,'2023-06-06 16:53:27','2023-06-06 16:53:27');
/*!40000 ALTER TABLE `users` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `users_roles`
--

DROP TABLE IF EXISTS `users_roles`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `users_roles` (
  `username` varchar(255) DEFAULT NULL,
  `role_id` int DEFAULT NULL,
  KEY `username` (`username`),
  KEY `role_id` (`role_id`),
  CONSTRAINT `users_roles_ibfk_1` FOREIGN KEY (`username`) REFERENCES `users` (`username`),
  CONSTRAINT `users_roles_ibfk_2` FOREIGN KEY (`role_id`) REFERENCES `roles` (`role_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `users_roles`
--

LOCK TABLES `users_roles` WRITE;
/*!40000 ALTER TABLE `users_roles` DISABLE KEYS */;
INSERT INTO `users_roles` VALUES ('scot-admin',2);
/*!40000 ALTER TABLE `users_roles` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `vuln_feeds`
--

DROP TABLE IF EXISTS `vuln_feeds`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `vuln_feeds` (
  `vuln_feed_id` int NOT NULL AUTO_INCREMENT,
  `owner` text COLLATE utf8mb4_unicode_ci NOT NULL,
  `tlp` enum('unset','white','green','amber','red','black','clear','amber_strict') COLLATE utf8mb4_unicode_ci NOT NULL,
  `status` enum('open','promoted','closed') COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `subject` text COLLATE utf8mb4_unicode_ci,
  `view_count` int NOT NULL,
  `message_id` text COLLATE utf8mb4_unicode_ci,
  `created_date` datetime DEFAULT NULL,
  `modified_date` datetime NOT NULL,
  PRIMARY KEY (`vuln_feed_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `vuln_tracks`
--

DROP TABLE IF EXISTS `vuln_tracks`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `vuln_tracks` (
  `vuln_track_id` int NOT NULL AUTO_INCREMENT,
  `owner` text COLLATE utf8mb4_unicode_ci NOT NULL,
  `tlp` enum('unset','white','green','amber','red','black','clear','amber_strict') COLLATE utf8mb4_unicode_ci NOT NULL,
  `status` enum('open','promoted','closed') COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `subject` text COLLATE utf8mb4_unicode_ci,
  `view_count` int NOT NULL,
  `message_id` text COLLATE utf8mb4_unicode_ci,
  `created_date` datetime DEFAULT NULL,
  `modified_date` datetime NOT NULL,
  PRIMARY KEY (`vuln_track_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;
