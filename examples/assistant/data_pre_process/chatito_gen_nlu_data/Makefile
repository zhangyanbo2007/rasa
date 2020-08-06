help:
	@echo "    train-nlu"
	@echo "        Train the natural language understanding using Rasa NLU."
	@echo "    train-core"
	@echo "        Train a dialogue model using Rasa core."
	@echo "    run"
	@echo "        Runs the bot on the command line."
	@echo "    run-api"
	@echo "        Runs the bot as a server."

run_taskbot_generate_data:
	npx chatito train_ergou_task_bot.chatito --format rasa --outputPath ../result/nlu_data/ergou_task
	rm ../result/nlu_data/ergou_task/rasa_dataset_testing.json
	python process_json.py ../result/nlu_data/ergou_task

run_kgbot_generate_data:
	npx chatito kgbot.chatito --format rasa --outputPath ../result/nlu_data/kg
	python process_json.py ../result/nlu_data/kg