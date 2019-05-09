from django.db import models


class Script(models.Model):
    name = models.CharField(max_length=100)
    script = models.TextField()

    def __unicode__(self):
        return self.name


class Operation(models.Model):
    user = models.CharField(max_length=50)
    start_time = models.DateTimeField(auto_now_add=True)
    biz = models.CharField(max_length=30)
    script = models.ForeignKey(Script)
    machine_numbers = models.IntegerField()
    celery_id = models.CharField(max_length=100)
    status = models.CharField(max_length=30, default="queue")
    argument = models.CharField(max_length=30, null=True, blank=True)

    log = models.TextField(null=True, blank=True)
    result = models.BooleanField(default=False)
    end_time = models.DateTimeField(null=True, blank=True)

    def __unicode__(self):
        return self.user + self.script.name

    class Meta:
        ordering = ['-id']

    def to_dict(self, biz_map=None):
        if biz_map is None:
            biz_map = {}
        return {
            'id': self.id,
            'user': self.user,
            'start_time': self.start_time.strftime("%Y-%m-%d %H:%M:%S"),
            'biz': biz_map.get(self.biz, self.biz),
            'script': self.script.name,
            'machine_numbers': self.machine_numbers,
            'celery_id': self.celery_id,
            'status': self.status,
            'argument': self.argument,
            'end_time': self.end_time.strftime("%Y-%m-%d %H:%M:%S") if self.end_time else "",
        }
