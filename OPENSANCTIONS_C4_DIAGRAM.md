# OpenSanctions AML System - C4 Architecture Diagrams

## C4 Level 1: System Context Diagram

```mermaid
C4Context
    title OpenSanctions AML System Context

    Person(compliance_officer, "Compliance Officer", "Reviews sanctions alerts and manages compliance")
    Person(developer, "Developer", "Integrates AML screening into applications")
    
    System_Ext(opensanctions, "OpenSanctions.org", "Consolidated sanctions data from 84 global authorities")
    System(aml_system, "AML Controller", "Anti-Money Laundering screening system using OpenSanctions data")
    System_Ext(banking_app, "Banking Application", "Core banking system requiring AML screening")
    System_Ext(crypto_exchange, "Crypto Exchange", "Digital asset trading platform")
    System_Ext(fintech_app, "FinTech Application", "Payment processing application")
    
    Rel(opensanctions, aml_system, "Provides daily sanctions data", "HTTPS/JSON")
    Rel(compliance_officer, aml_system, "Reviews alerts, manages sanctions", "Web UI")
    Rel(developer, aml_system, "Integrates screening APIs", "REST API")
    Rel(aml_system, banking_app, "Screens transactions", "REST API")
    Rel(aml_system, crypto_exchange, "Screens crypto addresses", "REST API")
    Rel(aml_system, fintech_app, "Validates parties", "REST API")
    
    UpdateLayoutConfig($c4ShapeInRow="3", $c4BoundaryInRow="2")
```

## C4 Level 2: Container Diagram

```mermaid
C4Container
    title OpenSanctions AML System Containers

    Person(compliance_officer, "Compliance Officer")
    Person(developer, "Developer")
    System_Ext(opensanctions, "OpenSanctions.org")
    
    Container_Boundary(c1, "AML Controller System") {
        Container(web_app, "Web Application", "React/Flask", "Admin dashboard for sanctions management")
        Container(api_app, "API Application", "Python/Flask", "REST API for AML screening services")
        Container(sanctions_service, "Sanctions Service", "Python", "Daily data fetch and processing from OpenSanctions")
        Container(screening_engine, "Screening Engine", "Python", "Real-time transaction screening logic")
        Container(database, "Database", "Supabase/PostgreSQL", "Stores sanctions entities and screening results")
        Container(search_index, "Search Service", "PostgreSQL FTS", "Full-text search for entity matching")
    }
    
    System_Ext(client_systems, "Client Systems", "Banking, FinTech, Crypto applications")
    
    Rel(compliance_officer, web_app, "Reviews alerts", "HTTPS")
    Rel(developer, api_app, "Integrates screening", "HTTPS/REST")
    Rel(client_systems, api_app, "Screens transactions", "HTTPS/REST")
    
    Rel(opensanctions, sanctions_service, "Downloads daily data", "HTTPS")
    Rel(sanctions_service, database, "Stores entities", "SQL")
    Rel(api_app, screening_engine, "Requests screening", "Function calls")
    Rel(screening_engine, database, "Queries entities", "SQL")
    Rel(screening_engine, search_index, "Searches names", "SQL")
    Rel(web_app, api_app, "Admin operations", "HTTPS")
    
    UpdateLayoutConfig($c4ShapeInRow="2", $c4BoundaryInRow="1")
```

## C4 Level 3: Component Diagram - Sanctions Service

```mermaid
C4Component
    title Sanctions Service Components

    Container_Ext(opensanctions, "OpenSanctions API", "External sanctions data source")
    Container_Ext(database, "Supabase Database", "PostgreSQL database")
    
    Container_Boundary(c1, "Sanctions Service") {
        Component(fetch_controller, "Fetch Controller", "Python", "Orchestrates daily data fetching")
        Component(senzing_parser, "Senzing Parser", "Python", "Parses Senzing JSON format")
        Component(entity_processors, "Entity Processors", "Python", "Processes 10 entity types")
        
        ComponentDb(person_processor, "Person Processor", "Python", "Handles 36,828 people entities")
        ComponentDb(org_processor, "Organization Processor", "Python", "Handles 16,330 organizations")
        ComponentDb(address_processor, "Address Processor", "Python", "Handles 20,227 addresses")
        ComponentDb(company_processor, "Company Processor", "Python", "Handles company entities")
        ComponentDb(crypto_processor, "Crypto Processor", "Python", "Handles 2,022 crypto wallets")
        ComponentDb(vessel_processor, "Vessel Processor", "Python", "Handles vessel entities")
        ComponentDb(aircraft_processor, "Aircraft Processor", "Python", "Handles aircraft entities")
        ComponentDb(security_processor, "Security Processor", "Python", "Handles 2,833 securities")
        ComponentDb(legal_processor, "Legal Entity Processor", "Python", "Handles 8,457 legal entities")
        ComponentDb(public_processor, "Public Body Processor", "Python", "Handles public bodies")
        
        Component(data_validator, "Data Validator", "Python", "Validates entity schemas")
        Component(storage_manager, "Storage Manager", "Python", "Manages database operations")
    }
    
    Rel(opensanctions, fetch_controller, "Downloads data", "HTTPS")
    Rel(fetch_controller, senzing_parser, "Raw JSON data")
    Rel(senzing_parser, entity_processors, "Parsed entities")
    
    Rel(entity_processors, person_processor, "Person entities")
    Rel(entity_processors, org_processor, "Organization entities")
    Rel(entity_processors, address_processor, "Address entities")
    Rel(entity_processors, company_processor, "Company entities")
    Rel(entity_processors, crypto_processor, "Crypto entities")
    Rel(entity_processors, vessel_processor, "Vessel entities")
    Rel(entity_processors, aircraft_processor, "Aircraft entities")
    Rel(entity_processors, security_processor, "Security entities")
    Rel(entity_processors, legal_processor, "Legal entities")
    Rel(entity_processors, public_processor, "Public entities")
    
    Rel(person_processor, data_validator, "Validates data")
    Rel(org_processor, data_validator, "Validates data")
    Rel(address_processor, data_validator, "Validates data")
    Rel(company_processor, data_validator, "Validates data")
    Rel(crypto_processor, data_validator, "Validates data")
    Rel(vessel_processor, data_validator, "Validates data")
    Rel(aircraft_processor, data_validator, "Validates data")
    Rel(security_processor, data_validator, "Validates data")
    Rel(legal_processor, data_validator, "Validates data")
    Rel(public_processor, data_validator, "Validates data")
    
    Rel(data_validator, storage_manager, "Validated entities")
    Rel(storage_manager, database, "Stores data", "SQL")
    
    UpdateLayoutConfig($c4ShapeInRow="3", $c4BoundaryInRow="1")
```

## C4 Level 4: Code Diagram - Entity Data Composition

```mermaid
classDiagram
    class BaseEntity {
        +String id
        +String schema
        +String caption
        +List~String~ countries
        +List~String~ topics
        +List~String~ datasets
        +Date first_seen
        +Date last_seen
        +Map properties
    }
    
    class Person {
        +String firstName
        +String lastName
        +Date birthDate
        +String birthPlace
        +String nationality
        +List~String~ passportNumbers
        +List~String~ idNumbers
        +validate()
        +normalize()
    }
    
    class Organization {
        +String name
        +Date incorporationDate
        +String registrationNumber
        +String taxNumber
        +String address
        +String country
        +String legalForm
        +validate()
        +normalize()
    }
    
    class Address {
        +String full
        +String street
        +String city
        +String region
        +String postalCode
        +String country
        +geocode()
        +validate()
    }
    
    class Company {
        +String name
        +String legalForm
        +String registrationNumber
        +String taxNumber
        +String sector
        +Integer employees
        +validate()
        +normalize()
    }
    
    class CryptoWallet {
        +String address
        +String currency
        +String holder
        +validateAddress()
        +getCurrencyType()
    }
    
    class Vessel {
        +String name
        +String imoNumber
        +String flag
        +Integer tonnage
        +String owner
        +validateIMO()
        +getVesselType()
    }
    
    class Aircraft {
        +String name
        +String registrationNumber
        +String model
        +String owner
        +validateTailNumber()
        +getAircraftType()
    }
    
    class Security {
        +String name
        +String isin
        +String cusip
        +String issuer
        +String securityType
        +validateISIN()
        +getSecurityInfo()
    }
    
    class LegalEntity {
        +String name
        +String email
        +String phone
        +String website
        +String legalForm
        +String status
        +validate()
        +normalize()
    }
    
    class PublicBody {
        +String name
        +String jurisdiction
        +String bodyType
        +String authority
        +String mandate
        +validate()
        +getJurisdictionInfo()
    }
    
    class SanctionsProcessor {
        +processEntity(BaseEntity)
        +validateSchema(String)
        +storeEntity(BaseEntity)
        +createSearchIndex(BaseEntity)
        +generateRelationships(BaseEntity)
    }
    
    BaseEntity <|-- Person
    BaseEntity <|-- Organization
    BaseEntity <|-- Address
    BaseEntity <|-- Company
    BaseEntity <|-- CryptoWallet
    BaseEntity <|-- Vessel
    BaseEntity <|-- Aircraft
    BaseEntity <|-- Security
    BaseEntity <|-- LegalEntity
    BaseEntity <|-- PublicBody
    
    SanctionsProcessor --> BaseEntity : processes
    SanctionsProcessor --> Person : "36,828 entities"
    SanctionsProcessor --> Organization : "16,330 entities"
    SanctionsProcessor --> Address : "20,227 entities"
    SanctionsProcessor --> Company : "entities"
    SanctionsProcessor --> CryptoWallet : "2,022 entities"
    SanctionsProcessor --> Vessel : "entities"
    SanctionsProcessor --> Aircraft : "entities"
    SanctionsProcessor --> Security : "2,833 entities"
    SanctionsProcessor --> LegalEntity : "8,457 entities"
    SanctionsProcessor --> PublicBody : "entities"
```

## Data Source Composition

```mermaid
mindmap
  root((OpenSanctions<br/>Consolidated<br/>264,518 entities))
    Primary Sources
      UN Security Council
        Global Framework
        Asset Freezing
        Travel Bans
      US OFAC
        SDN List
        Sectoral Sanctions
        CAPTA List
      EU Sanctions
        Consolidated List
        Country Sanctions
        Sectoral Measures
      UK OFSI
        Financial Sanctions
        Asset Freezes
        Investment Bans
    
    Entity Types
      People (36,828)
        Natural Persons
        Politically Exposed
        Criminal Associates
      Organizations (16,330)
        NGOs
        State Enterprises
        Terror Groups
      Addresses (20,227)
        Business Addresses
        Residential
        PO Boxes
      Companies
        Corporations
        Partnerships
        Joint Ventures
      
    Digital Assets
      Crypto Wallets (2,022)
        Bitcoin Addresses
        Ethereum Addresses
        Other Cryptocurrencies
      Securities (2,833)
        Bonds
        Stocks
        Derivatives
        
    Physical Assets
      Vessels
        Ships
        Boats
        Maritime Assets
      Aircraft
        Planes
        Helicopters
        Drones
        
    Legal Entities (8,457)
      Government Bodies
      Regulatory Agencies
      International Orgs
      Public Bodies
        Ministries
        Agencies
        Authorities
```

---

**C4 Diagram Version**: 1.0  
**Created**: 2025-08-22  
**Framework**: C4 Model with Mermaid  
**Focus**: Data Composition and System Architecture