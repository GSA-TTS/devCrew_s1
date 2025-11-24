workspace "E-Commerce Platform" {
    name "E-Commerce Platform"
    description "Architecture for online retail system"

    model {
        // People/Actors
        customer = person "Customer" "End user who purchases products"
        admin = person "Admin" "System administrator"

        // Software Systems
        ecommerce = softwareSystem "E-Commerce System" "Main platform" {
            // Containers
            webApp = container "Web Application" "Customer-facing web app" "React + TypeScript" {
                // Components
                productCatalog = component "Product Catalog" "Displays products" "React"
                shoppingCart = component "Shopping Cart" "Manages cart" "React + Redux"
                checkout = component "Checkout" "Processes orders" "React"
            }

            apiGateway = container "API Gateway" "Routes API requests" "Kong Gateway" {
                router = component "Router" "Routes requests" "Lua"
                auth = component "Authenticator" "Validates tokens" "JWT"
            }

            orderService = container "Order Service" "Handles orders" "Node.js + Express" {
                orderController = component "Order Controller" "REST endpoints" "Express"
                orderProcessor = component "Order Processor" "Business logic" "Node.js"
            }

            paymentService = container "Payment Service" "Processes payments" "Python + FastAPI"

            database = container "Database" "Stores data" "PostgreSQL"
        }

        paymentGateway = softwareSystem "Payment Gateway" "External payment processor" {
        }

        // Relationships
        customer -> webApp : "Uses" "HTTPS"
        customer -> ecommerce : "Purchases from"
        admin -> webApp : "Manages" "HTTPS"

        webApp -> apiGateway : "Makes API calls" "HTTPS/JSON"
        apiGateway -> orderService : "Routes to" "HTTP"
        apiGateway -> paymentService : "Routes to" "HTTP"

        orderService -> database : "Reads/Writes" "PostgreSQL"
        paymentService -> database : "Reads/Writes" "PostgreSQL"
        paymentService -> paymentGateway : "Processes payment" "HTTPS"

        // Component relationships
        productCatalog -> orderController : "Fetches products" "REST"
        shoppingCart -> orderController : "Creates order" "REST"
        checkout -> orderController : "Submits order" "REST"

        router -> auth : "Validates request" "Internal"
        auth -> orderController : "Forwards request" "HTTP"

        orderController -> orderProcessor : "Delegates to" "Function call"
    }

    views {
        systemContext ecommerce "System Context View" {}
        container ecommerce "Container View" {}
        component webApp "Component View - Web App" {}
    }
}
