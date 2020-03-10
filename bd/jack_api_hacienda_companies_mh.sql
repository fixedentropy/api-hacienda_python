-- MySQL dump 10.13  Distrib 8.0.19, for Win64 (x86_64)
--
-- Host: localhost    Database: jack_api_hacienda
-- ------------------------------------------------------
-- Server version	8.0.19

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `companies_mh`
--

DROP TABLE IF EXISTS `companies_mh`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `companies_mh` (
  `id` int NOT NULL AUTO_INCREMENT,
  `user_mh` varchar(100) DEFAULT NULL,
  `pass_mh` varchar(100) DEFAULT NULL,
  `signature` blob,
  `logo` longblob,
  `pin_sig` varchar(4) DEFAULT NULL,
  `company_api` int DEFAULT NULL,
  `env` varchar(45) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `id_idx` (`company_api`),
  CONSTRAINT `id` FOREIGN KEY (`company_api`) REFERENCES `companies` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=13 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `companies_mh`
--

LOCK TABLES `companies_mh` WRITE;
/*!40000 ALTER TABLE `companies_mh` DISABLE KEYS */;
INSERT INTO `companies_mh` VALUES (10,'089vvvvv8@prod.comprobanteselectronicos.go.cr','d=kFt+4fA|!|R/P-*^#LYYu','','','998',37,'api-prod'),(11,'05v8@prod.comprobanteselectronicos.go.cr','d=kFt+4fA|!|R/P-*^#LYYu','',_binary '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WYY5cv2uyZvfP+Esrz2S6A+2L+9JdPOWB6RT0tT4EAazDzZ2hX0V+eCACrACFQaj27eKhHPQYkvxG2/fEPJQ7LMwvoJ9NZ8BFiJ9QpMW0IprFXN6lip2MuiKLoYVYHuZS/8ApLwq4tz9O/i4fZ46i3lNoZaBufDZwK1r0TSRz6FI69w2lo0Po4TKE5+vfy8ZQDRxLNyoq+gNz4Wrb0hxdnQwfxb+wQc1JSvSFut36gAAAwA8aXXTQzW5Kib3DMH9PwdW80XpCvd5xgvU2N4MeHnu7y9LWrWAAAMAPHCDhSGDMWec/YbxFIlJmdcFaIAbwt9KiNI8eZhraBrMiv8AjT5BGfdX67zDUe97mnVTtJYa9/T8o1/KN23MqdlAmGs3Y7D5EvVd7fuZS27K/YZ25nV0EWBDE43aXYGB1DoH+EX3isrbmvLj+7mXmnnBvN/z5HcvehZLtxWr+zKL+nv6T6t9n4mXeT4FH02qC9iGJUpwNRbz6jKtzajv+kxs+uuryBQBV0Jij/ldoZIaHyUpIGazX62slA4X8sD9ywBLtI7LCXefUy2RQTrrE/jbNKzjDyzghAqyCUP9NpBr9Z/8fJt1jP8AYS60fzqfqWT/ADnhAqgiaPTEJeQWsT90z/Upx3/cM0X8tzaK9Zt/UqKvkX1g4WP7zYJjfq93ykRXk8zOX/nO5nge35Sf0TedTPn6PsmXvzh/0czvSyQec+6ZFXnaUK1sf9vrKijsz40meTCJmzbmL3/9S//aAAwDAQACAAMAAAAQ8888888888888888888888888888888888888888888888888888888888888888888888888888888888888888888888888888888888888888888888888888888888888888888888888888888888888888888888888888888w88888888888888888888888888888888888888888888117cgiQWG888888888888888888888888888888888888888wxX6egZlMMWPe0888888888888888888888888888888888885qzytgZbB4e/wD+tnuvPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPOPdedcxERf3v8hiQjeEvPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPK7WhfUP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','998',38,'api-prod'),(12,'0666@prod.comprobanteselectronicos.go.cr','d=kFt+4fA|!|R/P-*^#LYYu','',_binary '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','998',39,'api-prod');
/*!40000 ALTER TABLE `companies_mh` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2020-03-09 18:49:30
