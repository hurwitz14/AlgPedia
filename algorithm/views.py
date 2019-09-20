# Create your views here.
from algorithm.ContactForm import ContactForm
from algorithm.UserCreateForm import UserCreateForm
from algorithm.controllers import *
from algorithm.algorithmForm import AlgorithmForm
from algorithm.forms import FiltersAlgorithm, FiltersClassification
from algorithm.models import Paradigm, Implementation
from django.contrib import auth
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, redirect
from django.template import Context, RequestContext
from django.template.loader import get_template
from extractor.Bootstrapping import Bootstrapper
import json
import re

# get_all_classifications_name_link, wipe_database, is_database_empty, get_classification_by_id

def show_main_page(request):
    ctx = {'logged':  request.user.is_authenticated,
           'message' : 'Welcome to AlgPedia - the free encyclopedia that anyone can edit.',
           'top5_algorithms' : get_top5_algorithms(),
           'top5_users' : get_top5_users()}
    return render(request, 'index.html', ctx)

def sync_database(request):
    sync_message = ''
    # do this check for all the
    if(is_database_empty()):
        boot_strapper = Bootstrapper()
        boot_strapper.doDatabaseImporting()
        sync_message = 'Synched!'
    else:
        sync_message = 'Nothing to synch here!'


    t = get_template('default_debug.html')
    ctx = Context({'message' : sync_message})
    html = t.render(ctx)

    return HttpResponse(html)

def clear_database(request):
    wipe_database()

    t = get_template('default_debug.html')
    ctx = Context({'message' : 'Database Clean!'})
    html = t.render(ctx)

    return HttpResponse(html)


def signin(request):

    if request.method == 'POST':
        form = UserCreateForm(request.POST)
        if form.is_valid():
            new_user = form.save()
            ctx = {'logged':  request.user.is_authenticated}
            return redirect(profile)
        else:
            c = {'logged':  request.user.is_authenticated, 'form' : form}
            #c.update(request)
            return render(request, 'accounts/signin.html', c)
    else:
        c = {'logged':  request.user.is_authenticated, 'form' : UserCreateForm()}
        #c.update(request)
        return render(request, "accounts/signin.html", c)

def logout(request):
    auth.logout(request)
    ctx = {'logged':  request.user.is_authenticated, 'logout': True}
    return render(request, 'default_debug.html', ctx)

def about(request):
    ctx = {'logged':  request.user.is_authenticated}
    return render(request, 'about.html', ctx)


def advanced_search(request):
    ctx = {'logged': request.user.is_authenticated}
    if request.method == 'POST':
        searchwords = (request.POST['ad_search_input'])
    return render(request, 'search.html', ctx)

def ontoviz(request):
    ctx = {'logged':  request.user.is_authenticated}
    return render(request, 'ontoviz.html', ctx)

def contact(request):
    if request.method == 'POST':
        recipients = ['thaisnviana@gmail.com']
        # try:
        # 	send_mail(request.POST['subject'], request.POST['message'], request.POST['sender'], recipients, fail_silently=False)
        # except BadHeaderError:
        # 	return render(request, 'about.html', {'logged':  request.user.is_authenticated})
        return render(request, 'default_debug.html', {'logged':  request.user.is_authenticated})
    else:
        c = {'logged':  request.user.is_authenticated, 'form' : ContactForm()}
        c.update(request)
        return render(request, "contact.html", c)

@login_required
def profile(request):
    user_questions = get_all_userquestions()
    question_answers = []
    username = request.user.username
    classifications = get_all_classifications_name_link()
    programming_languages = get_all_programming_languages()
    universities = get_all_universities()
    # Recupero as perguntas com as respostas possiveis e as respostas que o usuario ja respondeu
    for user_question in user_questions :
        question_answers.append({"q": user_question, "qa" : get_questionaswer_by_question_id(user_question.id), "u_qa": get_userquestionanswer_by_question_id_and_user(username, user_question.id)})


    if request.method == "POST":
        if request.POST["universities"]:
            u = float(request.POST["universities"])
            reputation= 190 - u
            u_university = get_university_by_position(request.POST["universities"])
            save_university(username, u_university)
        # Insere as respostas para as perguntas
        for q in user_questions:
            q_data = request.POST["profile_" + str(q.id)]
            if q_data:
                if q_data.isdigit():
                    int_q_answer_id = int(q_data)
                    insert_user_question_answer(username, q.id, int_q_answer_id)
            else:
                delete_user_question_answer(username, q.id)

        data = request.POST.getlist("classifications_interest")
        ids = []

        for classification_id in data:
            if classification_id.isdigit():
                int_c = int(classification_id)
                ids.append(int_c)

        # Insere as classificacoes de interesse
        update_classifications_interests(username, ids)
        # insert_classifications_interests(username, ids)

        data = request.POST.getlist("classifications_knowledge")
        ids = []

        for classification_id in data:
            if classification_id.isdigit():
                int_c = int(classification_id)
                ids.append(int_c)

        update_classifications_proeficiencies(username, ids)
        # insert_classifications_proeficiencies(username, ids)

        data = request.POST.getlist("programming_languages")
        ids = []

        for programming_language_id in data:
            if programming_language_id.isdigit():
                int_c = int(programming_language_id)
                ids.append(int_c)

        # Insere as linguagens de programcao que o usuario e proeficiente
        update_programming_languages_proeficiencies(username, ids)
    # insert_programming_languages_proeficiencies(username, ids)

    if request.is_ajax():
        return HttpResponse()

    # Recupero todas as classificacoes e linguagens de programacao que o usuario e proeficiente
    u_c_p = get_user_classifications_proeficiencies_ids(username)
    u_p_l_p = get_user_programming_languages_proeficiencies_ids(username)

    # Recupero todas as classificacoes que o usuario tem interesse
    u_c_i = get_user_classifications_interests_ids(username)

    c = {
        'logged':  request.user.is_authenticated,
        'name': request.user.username,
        'question_answers':  question_answers,
        'classifications': classifications,
        'user_classifications_interests': u_c_i,
        'user_classification_proeficiencies': u_c_p,
        'user_programming_languages_proeficiencies': u_p_l_p,
        'programming_languages': programming_languages,
        'universities': get_all_universities(),
        #'user_university' : get_user_univertisy(request.user.username),
        'user_university': '',
        'questions': get_all_userquestions()}

    #c.update(request)

    return render(request, 'accounts/profile.html', c)

def rules(request):
    ctx = {'logged':  request.user.is_authenticated}
    return render(request, 'rules.html', ctx)

def show_all_classifications(request):

    search = request.GET.get('search', None)

    username = str(request.user) if request.user.is_authenticated else None
    ordered_classifications = get_all_classifications_ordered_name_link(username, search)
    user_interested_classifications = get_user_interested_classifications(username)

    ordered_classifications = dict_diff(ordered_classifications, user_interested_classifications)

    ctx = {
        'classifications' : ordered_classifications,  # get_all_classifications_name_link(),
        'logged':  request.user.is_authenticated,
        'user_interested_classifications': user_interested_classifications,
        'filters': FiltersClassification(request.GET)
    }
    return render(request, 'display_all_classifications.html', ctx)


def show_all_algorithms(request):

    search = request.GET.get('search', None)
    classification_id = request.GET.get('classification', None)

    algorithms = get_all_algorithms(search, classification_id)

    ctx_variables = {}
    algs = [ (alg.get_show_url(), alg.name, alg.reputation) for alg in algorithms]
    algorithms = [{'link' : a[0], 'name' : a[1], 'reputation': a[2]} for a in algs]
    ctx_variables['algorithms'] = algorithms
    ctx_variables['logged'] = request.user.is_authenticated
    ctx_variables['filters'] = FiltersAlgorithm(request.GET)
    return render(request, 'display_all_algorithms.html', ctx_variables)

def show_all_paradigms(request):

    ps = Paradigm.objects.all().order_by("label")

    ctx_variables = {}
    paras = [ (p.label, p.get_show_url()) for p in ps]
    paradigms = [{'label' : a[0], 'link' : a[1]} for a in paras]
    ctx_variables['paradigms'] = paradigms
    ctx_variables['logged'] = request.user.is_authenticated
    return render(request, 'display_all_paradigms.html', ctx_variables)


def show_paradigm_by_id(request, id):
    paradigm = get_paradigm_by_id(int(id))
    ctx = {
        'paradigm' : paradigm,
        'programming_languages' : get_all_programming_languages(),
        'logged':  request.user.is_authenticated
    }
    return render(request, 'display_paradigm.html', ctx)



def show_algorithm_by_id(request, id):
    alg = get_algorithm_by_id(int(id))
    imps = get_implementations_by_alg_id(int(id))
    for imp in imps:
        imp.code = re.sub('<[^>]*>', '', imp.code)
        imp.code = re.sub('&([^;]+);', '', imp.code)

    impl_question_answers = []

    implementationquestions = get_all_implementationquestions()

    for implementation_question in implementationquestions :
        impl_question_answers.append({"i_q": implementation_question, "i_q_a" : get_questionaswer_by_question_id(implementation_question.id)})

    user_votes = []
    username = request.user.username
    # Only get the user votes when the user is logged in
    if username != '':
        user_votes = get_user_votes_by_algorithm(username, int(id))


    classification = alg.classification

    # Reading request to insert the vote of an user for a specific implementation
    if request.method == "POST":
        username = request.user.username
        impl_id = int(request.POST['implId'])
        implementation = Implementation.objects.get(id=impl_id)

        # Parsing JSON with questions ids and answers
        questions = json.loads(request.POST['questions'])

        reputation = 0
        for iq in questions:
            question_id = int(iq[u'id'])
            question_answer = int(iq[u'answerId'])
            result_set = insert_user_impl_question_answer(username, impl_id, question_id, question_answer)
            reputation += result_set[0]
            user_weight = result_set[1]

        # TODO: remove hardcode 12.
        reputation = reputation / 12  # 12 is the sum from all question weights

        implementation.save_reputation(reputation, user_weight)
        implementation.algorithm.calculate_reputation()
        add_user_point(username)
        return HttpResponse('success')

    # Try and create an rdf file for the required algorithm
    # returns the name of the file so we can show it later
    rdf_path= ""
    #rdf_path = try_create_algorithm_rdf(int(id))


    ctx_variables = {}

    ctx_variables['algorithm_name'] = alg.name.encode('cp850','replace').decode('cp850')
    ctx_variables['algorithm_tags'] = alg.tags.all()
    ctx_variables['algorithm_id'] = alg.id
    ctx_variables['algorithm_classification'] = classification.name
    ctx_variables['algorithm_about'] = alg.description
    ctx_variables['classification_algp_url'] = classification.get_show_url()
    # make_classification_link(classification.id)
    ctx_variables['classification_dbp_url'] = classification.uri
    ctx_variables['rdf_path'] = rdf_path
    ctx_variables['implementations'] = imps
    ctx_variables['logged'] = request.user.is_authenticated
    ctx_variables['impl_question_answers'] = impl_question_answers
    ctx_variables['user_votes'] = user_votes

    ctx_variables.update(request)

    return render(request, 'display_algorithm_by_id.html', ctx_variables)

@login_required
def insert_implementation(request, id):

    if request.method == 'POST':
        algorithm = get_algorithm_by_id(int(request.POST['algorithm_id']))
        p_lang = get_programming_language_by_id(int(request.POST['programming_languages']))
        implementation = insert_implementation_alg_p_lang(algorithm, p_lang, request.POST['algorithm_code'], False, request.user)
        add_user_point(request.user.username)
        return HttpResponseRedirect(algorithm.get_show_url())
    else:
        c = {'logged':  request.user.is_authenticated, 'programming_languages' : get_all_programming_languages(), 'algorithm' : get_algorithm_by_id(int(id))}
        c.update(request)
        return render(request, "add_algorithm_implementation.html", c)

def show_classification_by_id(request, id):
    classification = get_classification_by_id(int(id))
    algs = get_algorithms_by_classification(classification)
    algs_names = map(lambda alg: alg.name, algs)
    algs_reputations = map(lambda alg: alg.reputation, algs)

    algs = [
        {'name' : t[0], 'link' : t[1], 'reputation':t[2]} for t in
        zip(algs_names,
            [
                get_algorithm_display_url().replace('#', str(id)) for id in map(lambda alg: alg.id, algs)
                ],
            algs_reputations
            )
        ]

    top5_algs = get_top5_algorithms_by_classification(classification)
    ctx = {
        'classif' : classification,
        'top5_algorithms' : top5_algs,
        # 'algorithms' : algs,
        'algorithms' : dict_diff(algs, top5_algs),
        'logged':  request.user.is_authenticated
    }
    return render(request, 'display_classification.html', ctx)


@login_required
def insert_algorithm(request, id=None):
    c = {}
    if request.method == 'POST':
        instance = Algorithm(visible=False, user=request.user)
        form = AlgorithmForm(request.POST, instance=instance)
        if form.is_valid():
            algorithm = form.save()
            add_user_point(request.user.username)
        else:
            c['form'] = form
            return render(request, "add_algorithm.html", c)

        return HttpResponseRedirect(algorithm.get_show_url())
    else:
        c = {
            'form' : AlgorithmForm(initial={'classification': id}),
            'programming_languages' : get_all_programming_languages(),
            'logged':  request.user.is_authenticated
        }
        c.update(request)

        return render(request, "add_algorithm.html", c)


@login_required
@user_passes_test(lambda u: u.is_moderator(), login_url='/access_denied/')
def moderator_dashboard(request):
    ctx = {}
    user = request.user
    classifications = {}
    user_programming_languages_ids = get_user_programming_languages_proeficiencies_ids(user.username)
    implementations = Implementation.objects.filter(programming_language__in=user_programming_languages_ids, visible=False)
    for implementation in  implementations:

        try :
            classifications[implementation.algorithm.classification.name].append(implementation)
        except :
            classifications[implementation.algorithm.classification.name] = []
            classifications[implementation.algorithm.classification.name].append(implementation)

    ctx['classifications'] = classifications
    ctx['logged'] = request.user.is_authenticated
    return render(request, 'moderator_dashboard.html', ctx)
