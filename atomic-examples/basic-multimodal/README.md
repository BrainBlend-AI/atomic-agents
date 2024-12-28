# Basic Multimodal Example

This example demonstrates how to use the Atomic Agents framework to analyze images with text, specifically focusing on extracting structured information from nutrition labels using GPT-4 Vision capabilities.

## Features

1. Image Analysis: Process nutrition label images using GPT-4 Vision
2. Structured Data Extraction: Convert visual information into structured Pydantic models
3. Multi-Image Processing: Analyze multiple nutrition labels simultaneously
4. Comprehensive Nutritional Data: Extract detailed nutritional information including:
   - Basic nutritional facts (calories, fats, proteins, etc.)
   - Serving size information
   - Vitamin and mineral content
   - Product details

## Getting Started

1. Clone the main Atomic Agents repository:
   ```bash
   git clone https://github.com/BrainBlend-AI/atomic-agents
   ```

2. Navigate to the basic-multimodal directory:
   ```bash
   cd atomic-agents/atomic-examples/basic-multimodal
   ```

3. Install dependencies using Poetry:
   ```bash
   poetry install
   ```

4. Set up environment variables:
   Create a `.env` file in the `basic-multimodal` directory with the following content:
   ```env
   OPENAI_API_KEY=your_openai_api_key
   ```
   Replace `your_openai_api_key` with your actual OpenAI API key.

5. Run the example:
   ```bash
   poetry run python basic_multimodal/main.py
   ```

## Components

### 1. Nutrition Label Schema (`NutritionLabel`)
Defines the structure for storing nutrition information, including:
- Macronutrients (fats, proteins, carbohydrates)
- Micronutrients (vitamins and minerals)
- Serving information
- Product details

### 2. Input/Output Schemas
- `NutritionAnalysisInput`: Handles input images and analysis instructions
- `NutritionAnalysisOutput`: Structures the extracted nutrition information

### 3. Nutrition Analyzer Agent
A specialized agent configured with:
- GPT-4 Vision capabilities
- Custom system prompts for nutrition label analysis
- Structured data validation

## Example Usage

The example includes test images in the `test_images` directory:
- `nutrition_label_1.png`: Example nutrition label image
- `nutrition_label_2.jpg`: Another example nutrition label image

Running the example will:
1. Load the test images
2. Process them through the nutrition analyzer
3. Display structured nutritional information for each label

## Customization

You can modify the example by:
1. Adding your own nutrition label images to the `test_images` directory
2. Adjusting the `NutritionLabel` schema to capture additional information
3. Modifying the system prompt to focus on specific aspects of nutrition labels

## Contributing

Contributions are welcome! Please fork the repository and submit a pull request with your enhancements or bug fixes.

## License

This project is licensed under the MIT License. See the [LICENSE](../../LICENSE) file for details.
