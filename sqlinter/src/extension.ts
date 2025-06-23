import * as vscode from 'vscode';
import { exec } from 'child_process';
import { promisify } from 'util';
import * as path from 'path';


const execAsync = promisify(exec);
let decorationType: vscode.TextEditorDecorationType;

export function activate(context: vscode.ExtensionContext) {
    const extensionRootPath = context.extensionUri.fsPath;
    console.log('Congratulations, your extension "sqlinter" is now active!');
    console.log(`путь к расширению: ${extensionRootPath}`);

    decorationType = vscode.window.createTextEditorDecorationType({
        backgroundColor: 'rgba(100, 200, 100, 0.2)',
        border: '1px solid rgba(100, 200, 100, 0.7)'
    });
    //проверка наличия API ключа
    const config = vscode.workspace.getConfiguration('sqlinter');
    if (!config.get('openAiApiKey')) {
        vscode.window.showInformationMessage(
            'Для работы SQLinter требуется OpenAI API ключ. Запустите команду "SQLinter: Set API Key"',
            'Ввести ключ'
        ).then(selection => {
            if (selection) {
                vscode.commands.executeCommand('sqlinter.setApiKey');
            }
        });
    }

    //Получаем API ключ
    async function getOpenAIApiKey() {
        const config = vscode.workspace.getConfiguration('sqlinter');
        const apiKey = config.get<string>('openAiApiKey');
        console.log(`ApiKey: ${apiKey}`);

    if (!apiKey) {
        const action = await vscode.window.showErrorMessage(
            'OpenAI API ключ не найден', 
            'Ввести ключ'
        );
        
        if (action === 'Ввести ключ') {
            await vscode.commands.executeCommand('sqlinter.setApiKey');
        }
        return;
    }
    return apiKey;
}

    // Вынесенная функция для анализа SQL
    async function analyzeSqlInDocument(document: vscode.TextDocument) {
        const absoluteFilePath = document.fileName;
        const apiKey = await getOpenAIApiKey();
        console.log(`Обработан файл: ${absoluteFilePath}`);
        
        if (document.languageId === 'python' || document.fileName.endsWith('.py')) {
            try {
                const sqlQueries = await runPythonScript(extensionRootPath, absoluteFilePath, apiKey);
                console.log(sqlQueries);
                await highlightSqlQueries(document, sqlQueries);
                vscode.window.showInformationMessage(`Обработан файл: ${absoluteFilePath}`);
            } catch (error) {
                vscode.window.showErrorMessage(`Ошибка обработки ${absoluteFilePath}: ${error}`);
            }
        }
    }

    // Команда для установки API ключа
    const setApiKeyCommand = vscode.commands.registerCommand('sqlinter.setApiKey', async () => {
        const apiKey = await vscode.window.showInputBox({
            prompt: 'Введите ваш OpenAI API ключ',
            password: true, // Скрываем ввод
            ignoreFocusOut: true
        });

        if (apiKey) {
            // Сохраняем в глобальных настройках VS Code
            await vscode.workspace.getConfiguration('sqlinter').update(
                'openAiApiKey',
                apiKey,
                vscode.ConfigurationTarget.Global
            );
            vscode.window.showInformationMessage('API ключ успешно сохранён!')
            console.log(apiKey);
        }
    });

    const clearApiKeyCommand = vscode.commands.registerCommand('sqlinter.clearApiKey', async () => {
        await vscode.workspace.getConfiguration('sqlinter').update(
            'openAiApiKey',
            undefined,
            vscode.ConfigurationTarget.Global
        );
        vscode.window.showInformationMessage('API ключ успешно удалён!');
    });

    // Новая команда для принудительного анализа SQL
    const analyzeSqlCommand = vscode.commands.registerCommand('sqlinter.analyzeSql', async () => {
        const activeEditor = vscode.window.activeTextEditor;
        
        if (!activeEditor) {
            vscode.window.showWarningMessage('Нет активного файла для анализа');
            return;
        }

        const document = activeEditor.document;
        
        // Проверяем, что это Python файл
        if (document.languageId !== 'python' && !document.fileName.endsWith('.py')) {
            vscode.window.showWarningMessage('SQLinter работает только с Python файлами');
            return;
        }

        // Сохраняем файл перед анализом
        if (document.isDirty) {
            await document.save();
            vscode.window.showInformationMessage('Файл сохранён. Запуск анализа...');
        } else {
            vscode.window.showInformationMessage('Запуск анализа SQL...');
        }

        // Запускаем анализ
        await analyzeSqlInDocument(document);
    });

    //обработка сохранения
    const saveDisposable = vscode.workspace.onDidSaveTextDocument(async (document) => {
        await analyzeSqlInDocument(document);
    });

    // Добавляем в подписки для очистки при деактивации
    context.subscriptions.push(saveDisposable);
    context.subscriptions.push(setApiKeyCommand);
    context.subscriptions.push(clearApiKeyCommand);
    context.subscriptions.push(analyzeSqlCommand);

    //базовый хеллоу ворлд
    const disposable = vscode.commands.registerCommand('sqlinter.helloWorld', () => {
		console.log('Hello World from SQLinter!');
        vscode.window.showInformationMessage('Hello World from SQLinter!');
    });
    context.subscriptions.push(disposable);
}

async function runPythonScript(rootPath: string, filePath: string, apiKey?: string) {
    // Получаем путь к директории с расширением
    const extensionDir = rootPath;
    
    // Формируем путь к Python-скрипту в той же директории
    const pythonScriptPath = path.join(extensionDir, 'scripts/main.py'); 
    console.log(`запущен скрипт: ${pythonScriptPath}`);
    const command = `python "${pythonScriptPath}" "${filePath}" ${apiKey ? `"${apiKey}"` : ''}`;
    
    // Явно устанавливаем кодировку UTF-8 для Windows
    const execOptions = {
        encoding: 'utf-8' as BufferEncoding,
        env: { 
            ...process.env, 
            PYTHONIOENCODING: 'utf-8'  // Принудительно устанавливаем UTF-8 для Python
        }
    };
    
    const { stdout, stderr } = await execAsync(command, execOptions);
    
    const outputChannel = vscode.window.createOutputChannel('Python Output');

    outputChannel.appendLine(stdout);
    if (stderr) outputChannel.appendLine(`Ошибки: ${stderr}`);
    outputChannel.show();
    
    try {
        // Парсим JSON
        const result = JSON.parse(stdout);
        if (result.error) {
            throw new Error(result.error);
        }

        // result теперь содержит массив SQL-запросов
        return result as Array<{
            id: number;
            query: string;
            verdict: string;
            reason: string;
            correction: string;
            start: number;
            end: number;
            // Добавляем новые поля с информацией о позициях
            start_line?: number;
            start_column?: number;
            end_line?: number;
            end_column?: number;
            line_content?: string;
        }>;

    } catch (error) {
        vscode.window.showErrorMessage(`Ошибка парсинга SQL: ${error}`);
        return [];
    }
}

async function highlightSqlQueries(document: vscode.TextDocument, extractedQueries: any[]) {
    decorationType.dispose();
    const diagnosticCollection = vscode.languages.createDiagnosticCollection('sql-queries');
    diagnosticCollection.clear();

    try {
        // 1. Запускаем Python-скрипт
        const queries = extractedQueries;

        // 2. Группируем запросы по типам вердиктов
        const correctQueries: vscode.DecorationOptions[] = [];
        const errorQueries: vscode.DecorationOptions[] = [];
        const warningQueries: vscode.DecorationOptions[] = [];
        const unknownQueries: vscode.DecorationOptions[] = [];

        // 3. Создаем типы декораций для разных вердиктов
        const correctDecorationType = vscode.window.createTextEditorDecorationType({
            backgroundColor: 'rgba(34, 197, 94, 0.2)', // зеленый для правильных
            border: '1px solid rgba(34, 197, 94, 0.7)',
            borderRadius: '2px'
        });

        const errorDecorationType = vscode.window.createTextEditorDecorationType({
            backgroundColor: 'rgba(239, 68, 68, 0.2)', // красный для ошибок
            border: '1px solid rgba(239, 68, 68, 0.7)',
            borderRadius: '2px'
        });

        const warningDecorationType = vscode.window.createTextEditorDecorationType({
            backgroundColor: 'rgba(245, 158, 11, 0.2)', // желтый для предупреждений
            border: '1px solid rgba(245, 158, 11, 0.7)',
            borderRadius: '2px'
        });

        const unknownDecorationType = vscode.window.createTextEditorDecorationType({
            backgroundColor: 'rgba(107, 114, 128, 0.2)', // серый для неопределенных
            border: '1px solid rgba(107, 114, 128, 0.7)',
            borderRadius: '2px'
        });

        // 4. Преобразуем позиции и группируем по типам
        queries.forEach((query: any) => {
            const startPos = document.positionAt(query.start);
            const endPos = document.positionAt(query.end);
            
            // Альтернативный способ через номер строки и колонку (если доступно)
            let range: vscode.Range;
            if (query.start_line && query.start_column !== undefined && query.end_line && query.end_column !== undefined) {
                // Используем точные номера строк и колонок
                const startPosAlt = new vscode.Position(query.start_line - 1, query.start_column);
                // VS Code Range использует exclusive end, поэтому добавляем +1 к end_column
                const endPosAlt = new vscode.Position(query.end_line - 1, query.end_column + 1);
                range = new vscode.Range(startPosAlt, endPosAlt);
                
                // Для отладки: сравниваем с абсолютными позициями
                if (process.env.NODE_ENV === 'development') {
                    console.log(`SQL Query ${query.id}: 
                        Absolute: ${startPos.line}:${startPos.character} - ${endPos.line}:${endPos.character}
                        Line/Col: ${startPosAlt.line}:${startPosAlt.character} - ${endPosAlt.line}:${endPosAlt.character}
                        Content: "${query.line_content?.substring(query.start_column, query.end_column + 1) || 'N/A'}"`);
                }
            } else {
                // Используем абсолютные позиции (старый способ)
                // Также добавляем +1 к конечной позиции для exclusive end
                const adjustedEndPos = document.positionAt(query.end + 1);
                range = new vscode.Range(startPos, adjustedEndPos);
            }
            
            const decoration = {
                range: range,
                hoverMessage: createHoverContent(query)
            };

            if (query.verdict === 'True') {
                correctQueries.push(decoration);
            } else if (query.verdict === 'Error') {
                errorQueries.push(decoration);
            } else if (query.verdict === 'Warning') {
                warningQueries.push(decoration);
            } else {
                unknownQueries.push(decoration);
            }
        });

        // 5. Применяем подсветку для каждого типа
        const editor = vscode.window.activeTextEditor;
        if (editor) {
            editor.setDecorations(correctDecorationType, correctQueries);
            editor.setDecorations(errorDecorationType, errorQueries);
            editor.setDecorations(warningDecorationType, warningQueries);
            editor.setDecorations(unknownDecorationType, unknownQueries);
        }

    } catch (error) {
        vscode.window.showErrorMessage(`Ошибка анализа SQL: ${error}`);
    }
}

function createHoverContent(query: any): vscode.MarkdownString {
    const md = new vscode.MarkdownString();
    
    // Заголовок с номером запроса
    md.appendMarkdown(`**SQL-запрос #${query.id + 1}**\n\n`);
    
    // Оригинальный запрос
    md.appendCodeblock(query.query, 'sql');
    
    // Определяем иконку и статус в зависимости от вердикта
    let statusIcon = '';
    let statusText = '';
    
    if (query.verdict === 'True') {
        statusIcon = '[OK]';
        statusText = 'Запрос корректен';
    } else if (query.verdict === 'Error') {
        statusIcon = '[ERROR]';
        statusText = 'Ошибка в запросе';
    } else if (query.verdict === 'Warning') {
        statusIcon = '[WARNING]';
        statusText = 'Запрос можно улучшить';
    } else {
        statusIcon = '[SQL]';
        statusText = 'SQL запрос обнаружен';
    }
    
    // Показываем анализ GPT
    md.appendMarkdown('### Анализ:\n');
    md.appendMarkdown(`${statusIcon} **Статус**: ${statusText}\n`);
    
    // Показываем описание от GPT
    if (query.reason && query.reason.trim() !== '') {
        md.appendMarkdown(`**Описание**: ${query.reason}\n`);
    }
    
    // Исправление от SQLinter (если есть)
    if (query.correction && query.correction.trim() !== '' && query.correction !== query.query) {
        md.appendMarkdown('\n### Предлагаемое исправление:\n');
        md.appendCodeblock(query.correction, 'sql');
    }
    
    return md;
}


export function deactivate() {}

