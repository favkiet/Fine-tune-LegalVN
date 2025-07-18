from openai import OpenAI
import asyncio
from pprint import pprint
from olmocr.pipeline import build_page_query
from multiprocessing import freeze_support

client = OpenAI(base_url="http://localhost:1234/v1", api_key="lm-studio", timeout=60)

async def main():
    query = await build_page_query("data/raw/luatvietnam-com/Công văn-1629-CT-CĐS.docx",
                                page=1,
                                target_longest_image_dim=1024,
                                target_anchor_text_len=6000)
    query['model'] = 'olmocr-7b-0225-preview'
    response = client.chat.completions.create(**query)
    print(response.choices[0].message.content)

if __name__ == '__main__':
    # This is required for multiprocessing to work correctly
    freeze_support()
    
    # Note: You need to install poppler (for pdfinfo command) first:
    # On macOS: brew install poppler
    # On Linux: apt-get install poppler-utils
    
    asyncio.run(main())