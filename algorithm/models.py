from django.db import models
from django.contrib.auth.models import User

class ProgrammingLanguage(models.Model):
	name = models.CharField(max_length=10)

	def __unicode__(self):
		return u'%s' % self.name

class Classification(models.Model):
	name = models.CharField(max_length=35)
	uri = models.URLField()

	def get_show_url(self):
		return "/show/cat/id/%i" % self.id

	def __unicode__(self):
		return u'%s' % self.name

class Algorithm(models.Model):
	name = models.CharField(max_length=30)
	description = models.TextField()
	classification = models.ForeignKey(Classification, null=True, blank=True)
	uri = models.URLField()
	visible = models.BooleanField()
	reputation = models.FloatField(default=0)

	user = models.ForeignKey(User, null=True, blank=True, verbose_name=u"Creator")

	def get_show_url(self):
		return "/show/alg/id/%i" % self.id

	def __unicode__(self):
		return u'%s' % self.name.lower().title()

class Implementation(models.Model):
	# an algorithm can have many implementations
	algorithm = models.ForeignKey(Algorithm)
	code = models.TextField()
	programming_language = models.ForeignKey(ProgrammingLanguage)
	visible = models.BooleanField()
	reputation = models.FloatField(default=0)

	user = models.ForeignKey(User, null=True, blank=True, verbose_name=u"Creator")

	def __unicode__(self):
		return u'%s' % self.code

	def get_show_url(self):
		return "/show/imp/id/%i" % self.id
	
	def save_reputation(self, reputation):
		# TODO: Fazer média de reputation
		pass


###################

# Relacionamento de interesse entre usuario e uma classificacao
class Interest(models.Model):
	classification = models.ForeignKey(Classification)
	user = models.ForeignKey(User)

# Classe base de proeficiencia do usuario em algo
class ProeficiencyScale(models.Model):
	user = models.ForeignKey(User)
	value = models.IntegerField()

class ProgrammingLanguageProeficiencyScale(ProeficiencyScale):
	programming_language = models.ForeignKey(ProgrammingLanguage)

class ClassificationProeficiencyScale(ProeficiencyScale):
	classification = models.ForeignKey(Classification)

# Questao de escala em relacao a algo
class Question(models.Model):
	text = models.TextField()
	priority = models.IntegerField()

# Respostas validas para as perguntas
class QuestionAnswer(models.Model):
	question = models.ForeignKey(Question)
	value = models.IntegerField()
	text = models.TextField()

# Pergunta em relacao ao usuario
class UserQuestion(Question):
	pass

class UserQuestionAnswer(models.Model):
	user = models.ForeignKey(User)
	user_question = models.ForeignKey(UserQuestion)
	question_answer = models.ForeignKey(QuestionAnswer)

# Pergunta em relacao a uma implementacao
class ImplementationQuestion(Question):
	pass

# Resposta de um usuario a uma determinada pergunta sobre uma determinada implementacao
class ImplementationQuestionAnswer(models.Model):
	user = models.ForeignKey(User)
	implementation = models.ForeignKey(Implementation)
	implementation_question = models.ForeignKey(ImplementationQuestion)
	question_answer = models.ForeignKey(QuestionAnswer)

	def save(self, *args, **kwargs):
		super(ImplementationQuestionAnswer, self).save(*args, **kwargs)

	def calculate_reputation(self):
		classifications_proeficiency = ClassificationProeficiencyScale.objects.filter(user=self.user).values_list('classification_id', flat=True)
		programminglanguage_proeficiency = ProgrammingLanguageProeficiencyScale.objects.filter(user=self.user).values_list('programming_language_id', flat=True)

		classification_weight = 1 if self.implementation.algorithm.classification.id in classifications_proeficiency else 0.5
		language_weight = 1 if self.implementation.programming_language.id in programminglanguage_proeficiency else 0.5
		user_profile_weight = self.user.userquestionanswer_set.get(question_answer__question_id=1).question_answer.value / 10
		question_weight = self.implementation_question.priority
		answer = self.question_answer.value / 5

		# this value must be (0-1) * [3,4,5]
		reputation = (answer * user_profile_weight * language_weight * classification_weight) * question_weight
		return reputation
