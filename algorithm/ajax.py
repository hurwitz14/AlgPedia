from algorithm.forms import TagForm
from algorithm.models import Implementation, algorithm, classification
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import Group
from django.urls import reverse
from django.shortcuts import get_object_or_404
from .tf_idf_query import query
import json

@login_required
def moderator_add(request):
	user = request.user
	g = Group.objects.get(name='Moderator')
	g.user_set.add(user)
	return json.dumps({'success': True})

@login_required
@user_passes_test(lambda u: u.is_moderator(), login_url='/access_denied/')
def moderator_action(request):
	action = request.POST.get('action')
	imp_id = request.POST.get('implementation_id')

	implementation = get_object_or_404(Implementation, id=imp_id)

	if action == 'accept':
		implementation.visible = True
		implementation.save()
	elif action == 'refuse':
		implementation.delete()

	return json.dumps({'success': True})

@login_required
def tag_add(request):
	ctx = {'success': True}
	form = TagForm(request.POST)
	if form.is_valid():
		tag = form.save()
		ctx['tag'] = {'id': tag.id, 'name': tag.name}
	else:
		ctx['success'] = False
		ctx['errors'] = form.errors

	return json.dumps(ctx)

def global_search_autocomplete(request):
	data = []
	term = request.GET.get('term', None)

	classifications = classification.objects.filter(name__icontains=term).order_by('name')[:10]
	for item in classifications:
		url = reverse('algorithm.views.show_classification_by_id', args=(item.id,))
		data.append({
			'label': item.name,
			'category': 'classfications',
			'category_label': u"Classifications",
			'url': url,
		})

	algorithms = algorithm.objects.filter(name__icontains=term).order_by('-reputation')[:10]
	for item in algorithms:
		url = reverse('algorithm.views.show_algorithm_by_id', args=(item.id,))
		data.append({
			'label': item.name,
			'category': 'algorithms',
			'category_label': u"Algorithms",
			'url': url,
		})

	related = query(term)
	for related_alg_name in related:
		related_alg = algorithm.objects.filter(name__icontains=related_alg_name).order_by('-reputation')[0]
		url = reverse('algorithm.views.show_algorithm_by_id', args=(related_alg.id,))
		data.append({
			'label': related_alg.name,
			'category': 'algorithms',
			'category_label': u"Algorithms",
			'url': url,
		})

	return json.dumps(data)
