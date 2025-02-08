

import org.jsoup.Jsoup;
import org.jsoup.nodes.Document;
import org.jsoup.nodes.Element;
import org.jsoup.select.Elements;
import org.apache.http.client.methods.HttpGet;
import org.apache.http.impl.client.CloseableHttpClient;
import org.apache.http.impl.client.HttpClients;
import org.apache.http.client.methods.CloseableHttpResponse;

import java.io.FileOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.nio.file.Files;
import java.nio.file.Paths;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.TimeUnit;

public class PDFScraper {
// Define constants for the number of concurrent threads, maximum retries, and connection timeout
private static final int THREAD_COUNT = 50; // Number of concurrent threads
private static final int MAX_RETRIES = 3; // Maximum number of retries for failed connections
private static final int TIMEOUT = 60000; // Timeout in milliseconds for connections

public static void main(String[] args) {
// Define the base URL of the website to scrape and the output directory to save the PDFs
String baseUrl = "https://papers.nips.cc&quot";
String outputDir = "D:/scraped-pdfs/"; // Change this path as needed

// Create an ExecutorService to manage a pool of threads for concurrent processing
ExecutorService executor = Executors.newFixedThreadPool(THREAD_COUNT);

try {
// Connect to the main page
System.out.println("Connecting to main page: " + baseUrl);
Document document = Jsoup.connect(baseUrl).timeout(TIMEOUT).get(); // Set a timeout for the connection
System.out.println("Successfully connected to main page.");

// Find all links to paper archives (year pages)
Elements yearLinks = document.select("a[href^=/paper_files/paper/]");
System.out.println("Found " + yearLinks.size() + " paper archive links.");

// Loop through each year link to process each year individually
for (Element yearLink : yearLinks) {
// Construct the URL for the year page
String yearUrl = baseUrl + yearLink.attr("href");
System.out.println("Processing paper archive: " + yearUrl);

try {
// Connect to the year page
Document yearPage = Jsoup.connect(yearUrl).timeout(TIMEOUT).get();
System.out.println("Successfully connected to year page: " + yearUrl);

// Find all paper links on the year page
Elements paperLinks = yearPage.select("ul.paper-list li a[href$=Abstract-Conference.html]");
System.out.println("Found " + paperLinks.size() + " paper links in year: " + yearUrl);

// Loop through each paper link and submit a task to the executor
for (Element paperLink : paperLinks) {
// Construct the URL for the paper's abstract page
String paperUrl = baseUrl + paperLink.attr("href");
// Submit a task to process the paper using the executor
executor.submit(() -> processPaper(baseUrl, paperUrl, outputDir));
}
} catch (IOException e) {
// Handle exceptions that occur while processing the year page
System.err.println("Failed to process year: " + yearUrl);
e.printStackTrace();
}
}

// Shut down the executor service and wait for all tasks to complete
executor.shutdown();
executor.awaitTermination(Long.MAX_VALUE, TimeUnit.NANOSECONDS);

} catch (IOException | InterruptedException e) {
// Handle exceptions that occur during the scraping process
System.err.println("An error occurred during the scraping process.");
e.printStackTrace();
}
}

// Method to process each paper link
private static void processPaper(String baseUrl, String paperUrl, String outputDir) {
String threadId = Thread.currentThread().getName(); // Get the name of the current thread
int attempts = 0; // Initialize the attempt counter
boolean success = false; // Flag to track if the process is successful

// Retry logic to handle intermittent network issues
while (attempts < MAX_RETRIES && !success) {
try {
System.out.println(threadId + " - Processing paper: " + paperUrl + " at " + java.time.LocalDateTime.now() + " (Attempt " + (attempts + 1) + ")");

// Connect to the paper's abstract page
Document paperPage = Jsoup.connect(paperUrl).timeout(TIMEOUT).get();
System.out.println(threadId + " - Successfully connected to paper page: " + paperUrl + " at " + java.time.LocalDateTime.now());

// Extract the paper title for the filename
String paperTitle = paperPage.select("title").text();
String sanitizedTitle = sanitizeFilename(paperTitle); // Sanitize the title to create a valid filename

// Find the PDF link on the abstract page
Element pdfLink = paperPage.selectFirst("a[href$=Paper-Conference.pdf]");
if (pdfLink != null) {
// Construct the URL for the PDF
String pdfUrl = baseUrl + pdfLink.attr("href");
System.out.println(threadId + " - Found PDF link: " + pdfUrl + " at " + java.time.LocalDateTime.now());

// Download the PDF with the sanitized title
downloadPDF(pdfUrl, outputDir, sanitizedTitle);
success = true; // Mark the process as successful
} else {
// If no PDF link is found, consider it handled and do not retry
System.out.println(threadId + " - No PDF link found on: " + paperUrl + " at " + java.time.LocalDateTime.now());
success = true; // Consider this as handled, no need to retry
}
} catch (IOException e) {
// Handle exceptions that occur while processing the paper
System.err.println("Failed to process paper: " + paperUrl + " at " + java.time.LocalDateTime.now() + " (Attempt " + (attempts + 1) + ")");
e.printStackTrace();
attempts++; // Increment the attempt counter
if (attempts >= MAX_RETRIES) {
// If the maximum number of retries is reached, give up on the paper
System.err.println(threadId + " - Giving up on paper: " + paperUrl + " after " + MAX_RETRIES + " attempts.");
}
}
}
}

// Method to download the PDF from the given URL
private static void downloadPDF(String pdfUrl, String outputDir, String fileName) throws IOException {
String threadId = Thread.currentThread().getName(); // Get the name of the current thread
CloseableHttpClient httpClient = HttpClients.createDefault(); // Create an HTTP client
HttpGet request = new HttpGet(pdfUrl); // Create an HTTP GET request for the PDF URL

// Execute the HTTP request and process the response
try (CloseableHttpResponse response = httpClient.execute(request)) {
String filePath = outputDir + fileName + ".pdf"; // Construct the file path for the PDF

// Ensure the output directory exists
Files.createDirectories(Paths.get(outputDir));

// Save the PDF to the output directory
try (InputStream inputStream = response.getEntity().getContent();
FileOutputStream outputStream = new FileOutputStream(filePath)) {
byte[] buffer = new byte[8192]; // Create a buffer for reading data
int bytesRead;
while ((bytesRead = inputStream.read(buffer)) != -1) {
// Write the read bytes to the output stream
outputStream.write(buffer, 0, bytesRead);
}
}
System.out.println(threadId + " - Saved PDF: " + filePath + " at " + java.time.LocalDateTime.now());
} finally {
httpClient.close(); // Close the HTTP client
}
}

// Method to sanitize the filename by replacing invalid characters with underscores
private static String sanitizeFilename(String filename) {
// Replace invalid filename characters with underscores
return filename.replaceAll("[\\\\/:*?\"<>|]", "_");
}
}

