"""
Sample HTML pages for testing accessibility audits.

Contains various HTML samples with different accessibility issues.
"""

# Page with multiple critical accessibility issues
CRITICAL_ISSUES_PAGE = """
<!DOCTYPE html>
<html>
<head>
    <title>Page with Critical Issues</title>
</head>
<body>
    <!-- Missing alt text -->
    <img src="logo.png">
    <img src="banner.jpg">

    <!-- Low contrast text -->
    <p style="color: #999; background-color: #fff;">
        This text has insufficient contrast
    </p>

    <!-- Form without labels -->
    <form>
        <input type="text" name="username">
        <input type="password" name="password">
        <button type="submit">Login</button>
    </form>

    <!-- Empty links -->
    <a href="#"></a>
    <a href="page.html"></a>

    <!-- Missing heading structure -->
    <h3>Section without h1 or h2</h3>

    <!-- Non-semantic clickable div -->
    <div onclick="doSomething()">Click me</div>

    <!-- Button without accessible name -->
    <button><i class="icon"></i></button>
</body>
</html>
"""

# Page with good accessibility
ACCESSIBLE_PAGE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Accessible Page Example</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            background-color: #fff;
        }
    </style>
</head>
<body>
    <header>
        <h1>Accessible Website</h1>
        <nav aria-label="Main navigation">
            <ul>
                <li><a href="/">Home</a></li>
                <li><a href="/about">About Us</a></li>
                <li><a href="/services">Services</a></li>
                <li><a href="/contact">Contact</a></li>
            </ul>
        </nav>
    </header>

    <main>
        <h2>Welcome</h2>
        <p>This is an accessible webpage that follows WCAG 2.1 guidelines.</p>

        <img src="team.jpg" alt="Our team collaborating in the office">

        <section>
            <h3>Contact Form</h3>
            <form>
                <label for="name">Full Name</label>
                <input type="text" id="name" name="name" required>

                <label for="email">Email Address</label>
                <input type="email" id="email" name="email" required>

                <label for="message">Message</label>
                <textarea id="message" name="message" required></textarea>

                <button type="submit">Send Message</button>
            </form>
        </section>

        <button aria-label="Search the website">
            <svg aria-hidden="true" focusable="false">
                <use xlink:href="#icon-search"></use>
            </svg>
        </button>
    </main>

    <footer>
        <p>&copy; 2024 Accessible Company. All rights reserved.</p>
    </footer>
</body>
</html>
"""

# Complex multi-section page
COMPLEX_PAGE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Complex Page with Mixed Issues</title>
</head>
<body>
    <header>
        <h1>E-Commerce Site</h1>
        <nav aria-label="Main navigation">
            <ul>
                <li><a href="/">Home</a></li>
                <li><a href="/products">Products</a></li>
                <li><a href="/cart">Cart</a></li>
            </ul>
        </nav>
    </header>

    <main>
        <!-- Good: Proper heading structure -->
        <h2>Featured Products</h2>

        <!-- Bad: Missing alt text on some images -->
        <article>
            <h3>Product 1</h3>
            <img src="product1.jpg" alt="Wireless headphones">
            <p>$99.99</p>
            <button>Add to Cart</button>
        </article>

        <article>
            <h3>Product 2</h3>
            <img src="product2.jpg"> <!-- Missing alt -->
            <p>$149.99</p>
            <button>Add to Cart</button>
        </article>

        <!-- Good: Form with labels -->
        <section>
            <h3>Newsletter Signup</h3>
            <form>
                <label for="newsletter-email">Email</label>
                <input type="email" id="newsletter-email" name="email" required>
                <button type="submit">Subscribe</button>
            </form>
        </section>

        <!-- Bad: Low contrast -->
        <aside style="color: #888; background: #ddd;">
            <p>Special offer: Use code SAVE10</p>
        </aside>

        <!-- Bad: Missing accessible name -->
        <button title="Like this product">
            <span class="icon-heart"></span>
        </button>

        <!-- Good: Accessible modal trigger -->
        <button aria-label="Open product details" data-modal="product-details">
            View Details
        </button>
    </main>

    <footer>
        <p>&copy; 2024 E-Commerce Co.</p>
    </footer>
</body>
</html>
"""

# Page with ARIA issues
ARIA_ISSUES_PAGE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <title>Page with ARIA Issues</title>
</head>
<body>
    <!-- Invalid ARIA attribute -->
    <div role="button" aria-invalid-attr="true">Click</div>

    <!-- ARIA role without required attributes -->
    <div role="tablist">
        <div role="tab">Tab 1</div>
        <div role="tab">Tab 2</div>
    </div>

    <!-- Missing aria-label on landmarks -->
    <nav>
        <ul>
            <li><a href="/">Home</a></li>
        </ul>
    </nav>

    <!-- Incorrect ARIA usage -->
    <button aria-pressed="yes">Toggle</button> <!-- Should be true/false -->

    <!-- Hidden accessible name -->
    <button>
        <span aria-hidden="true">Click me</span>
    </button>
</body>
</html>
"""

# Responsive page for viewport testing
RESPONSIVE_PAGE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Responsive Page</title>
    <style>
        .mobile-only { display: none; }
        .desktop-only { display: block; }

        @media (max-width: 768px) {
            .mobile-only { display: block; }
            .desktop-only { display: none; }
        }
    </style>
</head>
<body>
    <header>
        <h1>Responsive Design</h1>
    </header>

    <nav class="desktop-only" aria-label="Desktop navigation">
        <ul>
            <li><a href="/">Home</a></li>
            <li><a href="/about">About</a></li>
        </ul>
    </nav>

    <button class="mobile-only" aria-label="Open mobile menu">
        ☰
    </button>

    <main>
        <h2>Content</h2>
        <p>This page adapts to different screen sizes.</p>

        <!-- Image with srcset for responsive images -->
        <img
            src="image.jpg"
            srcset="image-small.jpg 400w, image-medium.jpg 800w, image-large.jpg 1200w"
            alt="Responsive image example"
        >
    </main>
</body>
</html>
"""

# Form with various input types
FORM_PAGE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Form Testing Page</title>
</head>
<body>
    <main>
        <h1>Registration Form</h1>

        <form>
            <!-- Text inputs with labels -->
            <label for="first-name">First Name</label>
            <input type="text" id="first-name" name="firstName" required>

            <label for="last-name">Last Name</label>
            <input type="text" id="last-name" name="lastName" required>

            <!-- Email input -->
            <label for="email">Email Address</label>
            <input type="email" id="email" name="email" required
                   aria-describedby="email-help">
            <span id="email-help">We'll never share your email.</span>

            <!-- Radio buttons -->
            <fieldset>
                <legend>Gender</legend>
                <label>
                    <input type="radio" name="gender" value="male">
                    Male
                </label>
                <label>
                    <input type="radio" name="gender" value="female">
                    Female
                </label>
                <label>
                    <input type="radio" name="gender" value="other">
                    Other
                </label>
            </fieldset>

            <!-- Checkboxes -->
            <label>
                <input type="checkbox" name="terms" required>
                I agree to the terms and conditions
            </label>

            <!-- Select dropdown -->
            <label for="country">Country</label>
            <select id="country" name="country">
                <option value="">Select a country</option>
                <option value="us">United States</option>
                <option value="ca">Canada</option>
                <option value="uk">United Kingdom</option>
            </select>

            <!-- Submit button -->
            <button type="submit">Register</button>
        </form>

        <!-- Form with missing labels (bad example) -->
        <h2>Login (Poor Accessibility)</h2>
        <form>
            <input type="text" placeholder="Username">
            <input type="password" placeholder="Password">
            <button>Login</button>
        </form>
    </main>
</body>
</html>
"""

# Page with tables
TABLE_PAGE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Table Testing Page</title>
</head>
<body>
    <main>
        <h1>Data Tables</h1>

        <!-- Accessible table -->
        <h2>Employee Data (Accessible)</h2>
        <table>
            <caption>Employee Information</caption>
            <thead>
                <tr>
                    <th scope="col">Name</th>
                    <th scope="col">Department</th>
                    <th scope="col">Email</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td>John Doe</td>
                    <td>Engineering</td>
                    <td>john@example.com</td>
                </tr>
                <tr>
                    <td>Jane Smith</td>
                    <td>Design</td>
                    <td>jane@example.com</td>
                </tr>
            </tbody>
        </table>

        <!-- Inaccessible table -->
        <h2>Sales Data (Poor Accessibility)</h2>
        <table>
            <tr>
                <td>Product</td>
                <td>Q1</td>
                <td>Q2</td>
            </tr>
            <tr>
                <td>Widget A</td>
                <td>$10,000</td>
                <td>$15,000</td>
            </tr>
        </table>
    </main>
</body>
</html>
"""


# Export all sample pages
SAMPLE_PAGES = {
    "critical_issues": CRITICAL_ISSUES_PAGE,
    "accessible": ACCESSIBLE_PAGE,
    "complex": COMPLEX_PAGE,
    "aria_issues": ARIA_ISSUES_PAGE,
    "responsive": RESPONSIVE_PAGE,
    "form": FORM_PAGE,
    "table": TABLE_PAGE,
}
