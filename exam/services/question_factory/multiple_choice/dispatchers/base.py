from exam.services.question_factory.multiple_choice.utils import divide_and_spread_remainder


class BaseSubtypeDispatcher:
    def __init__(self, generator_map):
        self.generator_map = generator_map

    def dispatch(self, quiz, participation, templates, count, verses, subtype):
        counts = divide_and_spread_remainder(count, len(templates))

        all_questions = []
        all_options = []
        all_messages = []
        leftover = 0

        for i, template in enumerate(templates):
            target_count = counts[i] + leftover
            if target_count <= 0:
                continue

            generator_factory = self.generator_map.get(template.code)
            if not generator_factory:
                continue
            generator_fn = generator_factory()

            if not generator_fn:
                all_messages.append(f"No generator for template {template.code}")
                continue

            result = generator_fn.generate(
                quiz=quiz,
                participation=participation,
                template=template,
                count=target_count,
                verses=verses,
                subtype=subtype,
            )

            questions = result.get('questions', [])
            options = result.get('options', [])
            message = result.get('message', '')

            generated = len(questions)
            leftover = max(target_count - generated, 0)

            all_questions.extend(questions)
            all_options.extend(options)
            all_messages.append(
                message if message else f"{generated} questions generated for subtype: {subtype.code}, template: {template.code}", )

        return {
            'message': all_messages,
            'questions': all_questions,
            'options': all_options
        }
