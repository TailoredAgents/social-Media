# OpenAI Image Generation API Reference

**Source**: https://platform.openai.com/docs/api-reference/images/createEdit

## Overview

Direct image generation using the GPT Image 1 model, which provides superior image quality and optimized performance for visual content creation.

## Usage

When you include the `image_generation` tool in your request, the model can decide when and how to generate images as part of the conversation, using your prompt and any provided image inputs.

The `image_generation_call` tool call result will include a base64-encoded image.

### Basic Image Generation

**JavaScript Example:**
```javascript
import OpenAI from "openai";
const openai = new OpenAI();

const response = await openai.responses.create({
    model: "gpt-image-1",
    input: "Generate an image of gray tabby cat hugging an otter with an orange scarf",
    tools: [{type: "image_generation"}],
});

// Save the image to a file
const imageData = response.output
  .filter((output) => output.type === "image_generation_call")
  .map((output) => output.result);

if (imageData.length > 0) {
  const imageBase64 = imageData[0];
  const fs = await import("fs");
  fs.writeFileSync("otter.png", Buffer.from(imageBase64, "base64"));
}
```

**Python Example:**
```python
from openai import OpenAI
import base64

client = OpenAI() 

response = client.responses.create(
    model="gpt-image-1",
    input="Generate an image of gray tabby cat hugging an otter with an orange scarf",
    tools=[{"type": "image_generation"}],
)

# Save the image to a file
image_data = [
    output.result
    for output in response.output
    if output.type == "image_generation_call"
]
    
if image_data:
    image_base64 = image_data[0]
    with open("otter.png", "wb") as f:
        f.write(base64.b64decode(image_base64))
```

### Tool Options

You can configure the following output options as parameters:

- **Size**: Image dimensions (e.g., 1024x1024, 1024x1536)
- **Quality**: Rendering quality (e.g. low, medium, high)
- **Format**: File output format
- **Compression**: Compression level (0-100%) for JPEG and WebP formats
- **Background**: Transparent or opaque

`size`, `quality`, and `background` support the `auto` option, where the model will automatically select the best option based on the prompt.

### Revised Prompt

When using the image generation tool, the mainline model will automatically revise your prompt for improved performance.

**Example Response:**
```json
{
  "id": "ig_123",
  "type": "image_generation_call",
  "status": "completed",
  "revised_prompt": "A gray tabby cat hugging an otter. The otter is wearing an orange scarf. Both animals are cute and friendly, depicted in a warm, heartwarming style.",
  "result": "..."
}
```

### Prompting Tips

- Image generation works best when you use terms like "draw" or "edit" in your prompt
- For combining images, use "edit the first image by adding this element from the second image" instead of "combine" or "merge"

## Multi-turn Editing

You can iteratively edit images by referencing previous response or image IDs.

### Using Previous Response ID

**JavaScript:**
```javascript
const response_fwup = await openai.responses.create({
  model: "gpt-image-1",
  previous_response_id: response.id,
  input: "Now make it look realistic",
  tools: [{ type: "image_generation" }],
});
```

**Python:**
```python
response_fwup = client.responses.create(
    model="gpt-image-1",
    previous_response_id=response.id,
    input="Now make it look realistic",
    tools=[{"type": "image_generation"}],
)
```

### Using Image ID

**JavaScript:**
```javascript
const response_fwup = await openai.responses.create({
  model: "gpt-image-1",
  input: [
    {
      role: "user",
      content: [{ type: "input_text", text: "Now make it look realistic" }],
    },
    {
      type: "image_generation_call",
      id: imageGenerationCalls[0].id,
    },
  ],
  tools: [{ type: "image_generation" }],
});
```

## Streaming

The image generation tool supports streaming partial images as the final result is being generated. Set the number of partial images (1-3) with the `partial_images` parameter.

**JavaScript Streaming:**
```javascript
const stream = await openai.images.generate({
  prompt: "Draw a gorgeous image of a river made of white owl feathers",
  model: "gpt-image-1",
  stream: true,
  partial_images: 2,
});

for await (const event of stream) {
  if (event.type === "image_generation.partial_image") {
    const idx = event.partial_image_index;
    const imageBase64 = event.b64_json;
    const imageBuffer = Buffer.from(imageBase64, "base64");
    fs.writeFileSync(`river${idx}.png`, imageBuffer);
  }
}
```

**Python Streaming:**
```python
stream = client.images.generate(
    prompt="Draw a gorgeous image of a river made of white owl feathers",
    model="gpt-image-1",
    stream=True,
    partial_images=2,
)

for event in stream:
    if event.type == "image_generation.partial_image":
        idx = event.partial_image_index
        image_base64 = event.b64_json
        image_bytes = base64.b64decode(image_base64)
        with open(f"river{idx}.png", "wb") as f:
            f.write(image_bytes)
```

## Supported Models

The image generation tool is supported for the following models:

- `gpt-4o`
- `gpt-image-1`
- `gpt-5`
- `gpt-5-mini`
- `gpt-4.1-mini`
- `o3`

**Note**: The model used for the image generation process is always `gpt-image-1`, but these models can be used as the mainline model in the Responses API as they can reliably call the image generation tool when needed.

## Force Image Generation

To force the image generation tool call, set the parameter:
```javascript
tool_choice: {"type": "image_generation"}
```

## Input Images

You can provide input images using file IDs or base64 data for image editing operations.

---
*Documentation saved from OpenAI API Reference*