import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'backend'))

from apify import Actor

async def main():
    async with Actor:
        actor_input = await Actor.get_input() or {}
        query = actor_input.get('query', '').strip()
        query_type = actor_input.get('queryType', 'auto')
        api_key = actor_input.get('apiKey', os.environ.get('SPIA_API_KEY', ''))
        serpapi_key = actor_input.get('serpapiKey', '')
        hibp_key = actor_input.get('hibpApiKey', '')

        if not query or len(query) < 2:
            await Actor.fail(status_message='Query too short (min 2 characters)')
            return

        await Actor.log.info(f'Scanning: {query} (type={query_type})')

        os.environ['SPIA_API_KEY'] = api_key
        if serpapi_key:
            os.environ['SPIA_SERPAPI_KEY'] = serpapi_key
        if hibp_key:
            os.environ['SPIA_HIBP_API_KEY'] = hibp_key

        from app.services.privacy_scanner import privacy_scanner, detect_query_type

        if query_type == 'auto':
            query_type = detect_query_type(query)

        data = await privacy_scanner.scan(query, query_type)

        await Actor.log.info(
            f'Scan complete: score={data["privacy_score"]}, '
            f'exposures={data["total_exposures"]}'
        )

        await Actor.push_data({
            'query': query,
            'query_type': query_type,
            'privacy_score': data['privacy_score'],
            'total_exposures': data['total_exposures'],
            'categories': data['categories'],
            'exposures': data['exposures'],
            'images': data.get('images', []),
            'data_sources': data['data_sources'],
            'recommendations': data.get('recommendations', []),
        })

        await Actor.log.info('Results pushed to dataset')

if __name__ == '__main__':
    asyncio.run(main())
