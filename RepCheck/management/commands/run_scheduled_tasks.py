from django.core.management.base import BaseCommand
from core.tasks import update_bills_cache, fetch_daily_congress_record
from legislation.tasks import fetch_and_process_bills_task

class Command(BaseCommand):
    help = 'Run scheduled tasks from multiple apps'

    def add_arguments(self, parser):
        parser.add_argument('task', type=str, help='Task to run')
        parser.add_argument('--force', action='store_true', help='Force update')

    def handle(self, *args, **options):
        task = options['task']
        
        if task == 'bills':
            result = fetch_and_process_bills_task.delay()
            self.stdout.write(f'Queued bills processing task: {result.id}')
            
        elif task == 'cache':
            force = options.get('force', False)
            result = update_bills_cache.delay(force_update=force)
            self.stdout.write(f'Queued cache update task: {result.id}')
            
        elif task == 'congress':
            result = fetch_daily_congress_record.delay()
            self.stdout.write(f'Queued congress record task: {result.id}')
            
        else:
            self.stdout.write(self.style.ERROR(f'Unknown task: {task}'))